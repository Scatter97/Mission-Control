import { Settings } from "lucide-react";

import type { MissionControlModule } from "../../app/modules/types";
import { SettingsPage } from "./SettingsPage";

export const settingsModule: MissionControlModule = {
  id: "settings",
  name: "Settings",

  navigation: [
    {
      id: "settings",
      label: "Settings",
      route: "/settings",
      icon: Settings,
      order: 1000
    }
  ],

  routes: [
    {
      path: "/settings",
      component: SettingsPage
    }
  ]
};