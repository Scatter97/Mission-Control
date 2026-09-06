import type { ComponentType } from "react";
import type { LucideIcon } from "lucide-react";

export interface ModuleRoute {
  path: string;
  component: ComponentType;
}

export interface NavigationItem {
  id: string;
  label: string;
  route: string;
  icon: LucideIcon;
  order?: number;
}

export interface MissionControlModule {
  id: string;
  name: string;
  routes?: ModuleRoute[];
  navigation?: NavigationItem[];
}