/** @odoo-module **/
/* global google */
import { Component, onWillStart, useEffect, useRef, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { renderToElement } from "@web/core/utils/render";
import { loadJS } from "@web/core/assets";
import { _t } from "@web/core/l10n/translation";

const STATE_COLORS = {
    available: "#28a745",
    reserved: "#fd7e14",
    sold: "#dc3545",
};
// Default view: focused on Nouakchott West (Tevragh Zeina / Ksar), where most
// listings sit. The map opens here and only re-frames when a filter narrows
// the set (see applyFilters).
const DEFAULT_CENTER = { lat: 18.095, lng: -15.985 };
const DEFAULT_ZOOM = 15;
// Teardrop pin path (24x36 viewport), anchored at the tip.
const PIN_PATH =
    "M12 0C5.37 0 0 5.37 0 12c0 9 12 24 12 24s12-15 12-24C24 5.37 18.63 0 12 0z";

export class RealEstateMap extends Component {
    static template = "real_estate_agency.MapAction";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        this.mapRef = useRef("map");
        this.allPlots = [];
        this.gmap = null;
        this.markers = [];
        this.infoWindow = null;

        this.state = useState({
            ready: false,
            error: "",
            shownCount: 0,
            totalCount: 0,
            moughataaOptions: [],
            lotissementOptions: [],
            filters: this._emptyFilters(),
        });

        onWillStart(async () => {
            const config = await this.orm.call(
                "real.estate.plot", "get_map_config", []
            );
            const apiKey = config.google_maps_api_key;
            if (!apiKey) {
                this.state.error = _t(
                    "Set the Google Maps API key in Settings → Real Estate to enable the map."
                );
                return;
            }
            await this.loadData();
            try {
                await loadJS(
                    "https://maps.googleapis.com/maps/api/js?key=" +
                        encodeURIComponent(apiKey) +
                        "&v=weekly"
                );
            } catch {
                this.state.error = _t(
                    "Could not load Google Maps. Check the API key, billing and your network."
                );
                return;
            }
            if (!window.google || !window.google.maps) {
                this.state.error = _t(
                    "Google Maps failed to initialise. The API key may be invalid or unauthorised."
                );
                return;
            }
            this.state.ready = true;
        });

        // Build the map once the container is in the DOM and Maps is ready.
        useEffect(
            () => {
                if (this.state.ready) {
                    this.initMap();
                }
                return () => this.clearMarkers();
            },
            () => [this.state.ready]
        );
    }

    _emptyFilters() {
        return {
            available: true,
            reserved: true,
            sold: true,
            moughataaId: "",
            lotissementId: "",
            priceMin: "",
            priceMax: "",
            surfaceMin: "",
            surfaceMax: "",
        };
    }

    // ---- data ---------------------------------------------------------
    async loadData() {
        const [plots, moughataas, lotissements] = await Promise.all([
            this.orm.searchRead(
                "real.estate.plot",
                ["|", ["latitude", "!=", 0], ["longitude", "!=", 0]],
                [
                    "reference", "name", "latitude", "longitude", "state",
                    "price", "currency_id", "surface", "neighborhood",
                    "lotissement_id", "moughataa_id", "image_128",
                ]
            ),
            this.orm.searchRead("real.estate.moughataa", [], ["name"]),
            this.orm.searchRead("real.estate.lotissement", [], ["name"]),
        ]);
        this.allPlots = plots;
        this.state.totalCount = plots.length;
        this.state.moughataaOptions = moughataas;
        this.state.lotissementOptions = lotissements;
    }

    // ---- map ----------------------------------------------------------
    initMap() {
        if (!this.mapRef.el || this.gmap) {
            return;
        }
        this.gmap = new google.maps.Map(this.mapRef.el, {
            center: DEFAULT_CENTER,
            zoom: DEFAULT_ZOOM,
            mapTypeId: "hybrid", // satellite imagery + street/place labels
            mapTypeControl: true,
            streetViewControl: false,
            fullscreenControl: true,
            gestureHandling: "greedy",
        });
        this.infoWindow = new google.maps.InfoWindow();
        this.gmap.addListener("contextmenu", (e) => this.onMapRightClick(e));
        this.applyFilters();
    }

    makeIcon(stateVal) {
        return {
            path: PIN_PATH,
            fillColor: STATE_COLORS[stateVal] || "#6c757d",
            fillOpacity: 1,
            strokeColor: "#ffffff",
            strokeWeight: 1.5,
            scale: 1.3,
            anchor: new google.maps.Point(12, 36),
        };
    }

    // ---- filtering (client-side) -------------------------------------
    filteredPlots() {
        const f = this.state.filters;
        const mId = parseInt(f.moughataaId);
        const lId = parseInt(f.lotissementId);
        const priceMin = parseFloat(f.priceMin);
        const priceMax = parseFloat(f.priceMax);
        const surfMin = parseFloat(f.surfaceMin);
        const surfMax = parseFloat(f.surfaceMax);
        return this.allPlots.filter((p) => {
            if (!f[p.state]) {
                return false;
            }
            if (!isNaN(mId) && (!p.moughataa_id || p.moughataa_id[0] !== mId)) {
                return false;
            }
            if (!isNaN(lId) && (!p.lotissement_id || p.lotissement_id[0] !== lId)) {
                return false;
            }
            if (!isNaN(priceMin) && p.price < priceMin) {
                return false;
            }
            if (!isNaN(priceMax) && p.price > priceMax) {
                return false;
            }
            if (!isNaN(surfMin) && p.surface < surfMin) {
                return false;
            }
            if (!isNaN(surfMax) && p.surface > surfMax) {
                return false;
            }
            return true;
        });
    }

    applyFilters() {
        if (!this.gmap) {
            return;
        }
        this.clearMarkers();
        const plots = this.filteredPlots();
        const bounds = new google.maps.LatLngBounds();
        for (const plot of plots) {
            const position = { lat: plot.latitude, lng: plot.longitude };
            const marker = new google.maps.Marker({
                position,
                map: this.gmap,
                icon: this.makeIcon(plot.state),
                title: plot.reference,
            });
            marker.addListener("click", async () => {
                const content = await this.makePopup(plot);
                this.infoWindow.setContent(content);
                this.infoWindow.open({ anchor: marker, map: this.gmap });
            });
            this.markers.push(marker);
            bounds.extend(position);
        }
        this.state.shownCount = plots.length;
        // Re-frame only when a filter is narrowing the set; otherwise keep the
        // default Nouakchott-West view instead of zooming out to fit everything.
        if (plots.length && this._filtersActive()) {
            this.gmap.fitBounds(bounds);
            google.maps.event.addListenerOnce(this.gmap, "idle", () => {
                if (this.gmap.getZoom() > 17) {
                    this.gmap.setZoom(17);
                }
            });
        }
    }

    _filtersActive() {
        const f = this.state.filters;
        return (
            !(f.available && f.reserved && f.sold) ||
            !!f.moughataaId ||
            !!f.lotissementId ||
            !!f.priceMin ||
            !!f.priceMax ||
            !!f.surfaceMin ||
            !!f.surfaceMax
        );
    }

    clearMarkers() {
        for (const marker of this.markers) {
            marker.setMap(null);
        }
        this.markers = [];
    }

    onFilterChange() {
        // Let t-model write the bound state first, then redraw the markers.
        Promise.resolve().then(() => this.applyFilters());
    }

    onResetFilters() {
        Object.assign(this.state.filters, this._emptyFilters());
        Promise.resolve().then(() => this.applyFilters());
    }

    // ---- popups -------------------------------------------------------
    _getImages(plotId) {
        if (!this._imageCache) {
            this._imageCache = {};
        }
        if (this._imageCache[plotId]) {
            return Promise.resolve(this._imageCache[plotId]);
        }
        return this.orm
            .call("real.estate.plot", "get_plot_images", [plotId])
            .then((imgs) => {
                this._imageCache[plotId] = imgs || [];
                return this._imageCache[plotId];
            });
    }

    async makePopup(plot) {
        const images = await this._getImages(plot.id);
        const el = renderToElement("real_estate_agency.PlotPopup", {
            plot,
            currencyName: plot.currency_id ? plot.currency_id[1] : "",
            lotissementName: plot.lotissement_id ? plot.lotissement_id[1] : "",
            moughataaName: plot.moughataa_id ? plot.moughataa_id[1] : "",
            priceLabel: (plot.price || 0).toLocaleString(),
            stateLabel: this.stateLabel(plot.state),
            stateColor: STATE_COLORS[plot.state] || "#6c757d",
            hasImages: images.length > 0,
            imgCount: images.length,
            firstImg: images.length ? "data:image/jpeg;base64," + images[0] : "",
        });
        // Wire the carousel arrows when there is more than one photo.
        if (images.length > 1) {
            let idx = 0;
            const imgEl = el.querySelector(".o_re_popup_img");
            const counter = el.querySelector(".o_re_counter");
            const show = (i) => {
                idx = (i + images.length) % images.length;
                imgEl.src = "data:image/jpeg;base64," + images[idx];
                counter.textContent = idx + 1 + " / " + images.length;
            };
            el.querySelector(".o_re_prev").addEventListener("click", (ev) => {
                ev.stopPropagation();
                show(idx - 1);
            });
            el.querySelector(".o_re_next").addEventListener("click", (ev) => {
                ev.stopPropagation();
                show(idx + 1);
            });
        }
        const btn = el.querySelector(".o_re_view_details");
        if (btn) {
            btn.addEventListener("click", () => this.openPlot(plot.id));
        }
        return el;
    }

    stateLabel(s) {
        return (
            {
                available: _t("Available"),
                reserved: _t("Reserved"),
                sold: _t("Sold"),
            }[s] || s
        );
    }

    openPlot(plotId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "real.estate.plot",
            res_id: plotId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    // ---- right-click quick create ------------------------------------
    onMapRightClick(e) {
        if (!e.latLng) {
            return;
        }
        const lat = e.latLng.lat();
        const lng = e.latLng.lng();
        this.action.doAction(
            {
                type: "ir.actions.act_window",
                res_model: "real.estate.plot",
                views: [[false, "form"]],
                target: "new",
                context: {
                    default_latitude: lat,
                    default_longitude: lng,
                },
            },
            { onClose: () => this.reload() }
        );
    }

    async reload() {
        await this.loadData();
        this.applyFilters();
    }
}

registry.category("actions").add("real_estate_agency.map", RealEstateMap);
