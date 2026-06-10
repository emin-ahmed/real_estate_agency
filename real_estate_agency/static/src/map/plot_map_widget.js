/** @odoo-module **/
/* global google */
import { Component, onWillStart, useEffect, useRef, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";
import { _t } from "@web/core/l10n/translation";

const DEFAULT_CENTER = { lat: 18.095, lng: -15.985 };

/**
 * Form view widget: a small Google map centred on the plot's coordinates with
 * a marker. In edit mode the marker is draggable (and clicking the map moves
 * it), writing latitude/longitude back to the record.
 */
export class PlotLocationMap extends Component {
    static template = "real_estate_agency.PlotLocationMap";
    static props = { ...standardWidgetProps };

    setup() {
        this.orm = useService("orm");
        this.mapRef = useRef("map");
        this.gmap = null;
        this.marker = null;
        this.state = useState({ ready: false, error: "" });

        onWillStart(async () => {
            const config = await this.orm.call(
                "real.estate.plot", "get_map_config", []
            );
            const key = config.google_maps_api_key;
            if (!key) {
                this.state.error = _t(
                    "Set the Google Maps API key in Settings → Real Estate."
                );
                return;
            }
            try {
                await loadJS(
                    "https://maps.googleapis.com/maps/api/js?key=" +
                        encodeURIComponent(key) +
                        "&v=weekly"
                );
            } catch {
                this.state.error = _t("Could not load Google Maps.");
                return;
            }
            if (window.google && window.google.maps) {
                this.state.ready = true;
            } else {
                this.state.error = _t("Google Maps failed to initialise.");
            }
        });

        useEffect(
            () => {
                if (this.state.ready) {
                    this.initMap();
                }
                return () => {
                    this.gmap = null;
                    this.marker = null;
                };
            },
            () => [this.state.ready]
        );

        // Keep the marker in sync when the coordinates change elsewhere
        // (e.g. typed into the latitude/longitude fields).
        useEffect(
            () => {
                const pos = this.currentPos();
                if (this.gmap && this.marker && pos) {
                    this.marker.setPosition(pos);
                    this.marker.setVisible(true);
                    this.gmap.panTo(pos);
                }
            },
            () => [this.lat, this.lng]
        );
    }

    get lat() {
        return this.props.record.data.latitude;
    }
    get lng() {
        return this.props.record.data.longitude;
    }

    currentPos() {
        if (!this.lat && !this.lng) {
            return null;
        }
        return { lat: this.lat, lng: this.lng };
    }

    initMap() {
        if (!this.mapRef.el || this.gmap) {
            return;
        }
        // Never let a Google Maps failure bubble up and break the form.
        try {
            const pos = this.currentPos();
            const editable = !this.props.readonly;
            this.gmap = new google.maps.Map(this.mapRef.el, {
                center: pos || DEFAULT_CENTER,
                zoom: pos ? 16 : 13,
                mapTypeId: "hybrid",
                mapTypeControl: true,
                streetViewControl: false,
                fullscreenControl: true,
                gestureHandling: "greedy",
            });
            this.marker = new google.maps.Marker({
                position: pos || DEFAULT_CENTER,
                map: this.gmap,
                draggable: editable,
                visible: Boolean(pos) || editable,
            });
            if (editable) {
                this.marker.addListener("dragend", (e) => this.setCoords(e.latLng));
                this.gmap.addListener("click", (e) => {
                    this.marker.setPosition(e.latLng);
                    this.marker.setVisible(true);
                    this.setCoords(e.latLng);
                });
            }
        } catch (e) {
            console.warn("Real Estate: on-form map could not initialise.", e);
        }
    }

    setCoords(latLng) {
        this.props.record.update({
            latitude: latLng.lat(),
            longitude: latLng.lng(),
        });
    }
}

export const plotLocationMap = {
    component: PlotLocationMap,
    fieldDependencies: [
        { name: "latitude", type: "float" },
        { name: "longitude", type: "float" },
    ],
};

registry.category("view_widgets").add("re_plot_location_map", plotLocationMap);
