/** @odoo-module */

import { Component } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";

export class ProductCard extends Component {
    static template = "point_of_sale.ProductCard";
    static props = {
        class: { String, optional: true },
        name: String,
        productId: Number,
        price: String,
        imageUrl: [String, Boolean],
        productInfo: { Boolean, optional: true },
        onClick: { type: Function, optional: true },
        onProductInfoClick: { type: Function, optional: true },
    };
    static defaultProps = {
        onClick: () => {},
        class: "",
    };
}