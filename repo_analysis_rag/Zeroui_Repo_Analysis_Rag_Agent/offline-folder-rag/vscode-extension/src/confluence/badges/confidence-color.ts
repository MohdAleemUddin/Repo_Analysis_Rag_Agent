/** US-18: Returns hex color for confidence percentage. Green >90%, Yellow 70-90%, Red <70%. */
export function getConfidenceColor(pct: number): string {
    if (pct > 90) return '#4CAF50';
    if (pct >= 70) return '#FFC107';
    return '#D32F2F';
}
