/** @odoo-module **/
/* global L */
import { Component, onWillStart, useEffect, useRef, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { renderToElement } from "@web/core/utils/render";
import { _t } from "@web/core/l10n/translation";

const STATE_COLORS = {
    available: "#28a745",
    reserved: "#fd7e14",
    sold: "#dc3545",
};
// Nouakchott centre (see CLAUDE.md) — used when no plots have coordinates.
const DEFAULT_CENTER = [18.0735, -15.9582];
const DEFAULT_ZOOM = 13;

export class RealEstateMap extends Component {
    static template = "real_estate_agency.MapAction";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        this.mapRef = useRef("map");
        this.allPlots = [];
        this.leafletMap = null;
        this.markerLayer = null;

        this.state = useState({
            loaded: false,
            shownCount: 0,
            totalCount: 0,
            moughataaOptions: [],
            lotissementOptions: [],
            filters: this._emptyFilters(),
        });

        onWillStart(() => this.loadData());

        // Create the Leaflet map once the container div is mounted; tear it
        // down on unmount. Mirrors addons/delivery .../map.js.
        useEffect(
            () => {
                this.initMap();
                return () => {
                    if (this.leafletMap) {
                        this.leafletMap.remove();
                        this.leafletMap = null;
                    }
                };
            },
            () => [this.state.loaded]
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
        this.state.loaded = true;
    }

    // ---- map ----------------------------------------------------------
    initMap() {
        if (!this.mapRef.el || this.leafletMap) {
            return;
        }
        this.leafletMap = L.map(this.mapRef.el).setView(DEFAULT_CENTER, DEFAULT_ZOOM);
        L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
            maxZoom: 19,
            attribution:
                '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        }).addTo(this.leafletMap);
        this.markerLayer = L.layerGroup().addTo(this.leafletMap);
        this.leafletMap.on("contextmenu", (ev) => this.onMapRightClick(ev));
        this.applyFilters();
    }

    makeIcon(stateVal) {
        const color = STATE_COLORS[stateVal] || "#6c757d";
        const html = `<svg width="26" height="38" viewBox="0 0 26 38" xmlns="http://www.w3.org/2000/svg">
            <path d="M13 0C5.82 0 0 5.82 0 13c0 9.5 13 25 13 25s13-15.5 13-25C26 5.82 20.18 0 13 0z"
                  fill="${color}" stroke="#ffffff" stroke-width="2"/>
            <circle cx="13" cy="13" r="4.5" fill="#ffffff"/></svg>`;
        return L.divIcon({
            className: "o_re_marker",
            html,
            iconSize: [26, 38],
            iconAnchor: [13, 38],
            popupAnchor: [0, -34],
        });
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
        if (!this.markerLayer) {
            return;
        }
        this.markerLayer.clearLayers();
        const plots = this.filteredPlots();
        const bounds = [];
        for (const plot of plots) {
            const latlng = [plot.latitude, plot.longitude];
            bounds.push(latlng);
            const marker = L.marker(latlng, { icon: this.makeIcon(plot.state) });
            marker.bindPopup(() => this.makePopup(plot), { minWidth: 220 });
            this.markerLayer.addLayer(marker);
        }
        this.state.shownCount = plots.length;
        if (bounds.length) {
            this.leafletMap.fitBounds(bounds, { padding: [40, 40], maxZoom: 16 });
        }
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
    makePopup(plot) {
        const el = renderToElement("real_estate_agency.PlotPopup", {
            plot,
            currencyName: plot.currency_id ? plot.currency_id[1] : "",
            lotissementName: plot.lotissement_id ? plot.lotissement_id[1] : "",
            moughataaName: plot.moughataa_id ? plot.moughataa_id[1] : "",
            priceLabel: (plot.price || 0).toLocaleString(),
            stateLabel: this.stateLabel(plot.state),
            stateColor: STATE_COLORS[plot.state] || "#6c757d",
        });
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
    onMapRightClick(ev) {
        const { lat, lng } = ev.latlng;
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
