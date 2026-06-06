/** @odoo-module **/
import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class RealEstateDashboard extends Component {
    static template = "real_estate_agency.Dashboard";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({ loaded: false, data: {} });

        onWillStart(async () => {
            this.state.data = await this.orm.call(
                "real.estate.plot", "get_dashboard_data", []
            );
            this.state.loaded = true;
        });
    }

    fmt(n) {
        return (n || 0).toLocaleString();
    }

    money(n) {
        const sym = this.state.data.currency_symbol || "";
        return this.fmt(Math.round(n || 0)) + " " + sym;
    }

    openPlots(domain, name) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: name,
            res_model: "real.estate.plot",
            domain: domain || [],
            views: [
                [false, "list"],
                [false, "kanban"],
                [false, "form"],
            ],
        });
    }

    openAll() {
        this.openPlots([], "All plots");
    }

    openState(s) {
        this.openPlots([["state", "=", s]], s);
    }
}

registry.category("actions").add("real_estate_agency.dashboard", RealEstateDashboard);
