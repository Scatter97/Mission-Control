import { FolderKanban } from "lucide-react";

import type { MissionControlModule } from "../../app/modules/types";
import { NewProjectPage } from "./pages/NewProjectPage";
import { ProjectDetailPage } from "./pages/ProjectDetailPage";
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
    },
    {
      path: "/projects/new",
      component: NewProjectPage
    },
    {
      path: "/projects/:id",
      component: ProjectDetailPage
    }
  ]
};
