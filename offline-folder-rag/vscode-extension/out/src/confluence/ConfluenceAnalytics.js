"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ConfluenceAnalytics = void 0;
const React = require("react");
const intelligence_dashboard_1 = require("./intelligence-dashboard");
const ConfluenceAnalytics = (props) => {
    return (React.createElement(intelligence_dashboard_1.IntelligenceDashboard, { metrics: props.metrics, learningProgress: props.learningProgress, intelligenceSummary: props.intelligenceSummary, successRate: props.successRate }));
};
exports.ConfluenceAnalytics = ConfluenceAnalytics;
