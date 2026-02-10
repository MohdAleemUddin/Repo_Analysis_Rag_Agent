"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.Onboarding = exports.FIRST_TIME_TOOLTIP_TEXT = exports.KEY = void 0;
exports.getOnboardingState = getOnboardingState;
exports.saveOnboardingState = saveOnboardingState;
exports.isFirstUse = isFirstUse;
exports.incrementUsage = incrementUsage;
exports.markTooltipShown = markTooltipShown;
exports.resetOnboarding = resetOnboarding;
const simple_language_json_1 = __importDefault(require("./simple-language.json"));
exports.KEY = "confluence-onboarding";
exports.FIRST_TIME_TOOLTIP_TEXT = simple_language_json_1.default.tooltips?.firstTime
    ?? simple_language_json_1.default.phrases?.firstInteraction?.buttonTooltip
    ?? "";
const MAX_TOOLTIP_SHOWN = 3;
const defaultState = { tooltipShown: 0, usageCount: 0 };
function getOnboardingState(context) {
    const raw = context.workspaceState.get(exports.KEY);
    if (raw && typeof raw.tooltipShown === "number" && typeof raw.usageCount === "number") {
        return { ...defaultState, ...raw };
    }
    return { ...defaultState };
}
function saveOnboardingState(context, state) {
    context.workspaceState.update(exports.KEY, state);
}
function isFirstUse(context) {
    return getOnboardingState(context).usageCount === 0;
}
function incrementUsage(context) {
    const state = getOnboardingState(context);
    state.usageCount += 1;
    saveOnboardingState(context, state);
}
function markTooltipShown(context) {
    const state = getOnboardingState(context);
    if (state.tooltipShown < MAX_TOOLTIP_SHOWN) {
        state.tooltipShown += 1;
        saveOnboardingState(context, state);
    }
}
function resetOnboarding(context) {
    saveOnboardingState(context, defaultState);
}
const Onboarding = () => null;
exports.Onboarding = Onboarding;
