"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getConfidenceColor = getConfidenceColor;
/** US-18: Returns hex color for confidence percentage. Green >90%, Yellow 70-90%, Red <70%. */
function getConfidenceColor(pct) {
    if (pct > 90)
        return '#4CAF50';
    if (pct >= 70)
        return '#FFC107';
    return '#D32F2F';
}
