import * as React from "react";
import * as vscode from "vscode";
import messages from "./simple-language.json";

export const KEY = "confluence-onboarding";
export const FIRST_TIME_TOOLTIP_TEXT: string =
  (messages as { tooltips?: { firstTime?: string }; phrases?: { firstInteraction?: { buttonTooltip?: string } } }).tooltips?.firstTime
  ?? (messages as { phrases?: { firstInteraction?: { buttonTooltip?: string } } }).phrases?.firstInteraction?.buttonTooltip
  ?? "";
const MAX_TOOLTIP_SHOWN = 3;

export interface OnboardingState {
  tooltipShown: number;
  usageCount: number;
}

const defaultState: OnboardingState = { tooltipShown: 0, usageCount: 0 };

export function getOnboardingState(
  context: vscode.ExtensionContext
): OnboardingState {
  const raw = context.workspaceState.get<OnboardingState>(KEY);
  if (raw && typeof raw.tooltipShown === "number" && typeof raw.usageCount === "number") {
    return { ...defaultState, ...raw };
  }
  return { ...defaultState };
}

export function saveOnboardingState(
  context: vscode.ExtensionContext,
  state: OnboardingState
): void {
  context.workspaceState.update(KEY, state);
}

export function isFirstUse(context: vscode.ExtensionContext): boolean {
  return getOnboardingState(context).usageCount === 0;
}

export function incrementUsage(context: vscode.ExtensionContext): void {
  const state = getOnboardingState(context);
  state.usageCount += 1;
  saveOnboardingState(context, state);
}

export function markTooltipShown(context: vscode.ExtensionContext): void {
  const state = getOnboardingState(context);
  if (state.tooltipShown < MAX_TOOLTIP_SHOWN) {
    state.tooltipShown += 1;
    saveOnboardingState(context, state);
  }
}

export function resetOnboarding(context: vscode.ExtensionContext): void {
  saveOnboardingState(context, defaultState);
}

export const Onboarding: React.FC = () => null;
