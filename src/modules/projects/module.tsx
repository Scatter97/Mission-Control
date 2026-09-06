import { FolderKanban } from "lucide-react";

import type { MissionControlModule } from "../../app/modules/types";
import { ProjectsPage } from "./pages/ProjectsPage";

export const projectsModule: MissionControlModule = {
  id: "projects",
  name: "Projects",

  navigation: [
    {
      id: "projects",
      label: "Projects",
      route: "/projects",
      icon: FolderKanban,
      order: 10
    }
  ],

  routes: [
    {
      path: "/projects",
      component: ProjectsPage
    }
  ]
};