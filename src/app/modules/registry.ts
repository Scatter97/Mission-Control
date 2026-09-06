import type {
  MissionControlModule,
  ModuleRoute,
  NavigationItem
} from "./types";

import { projectsModule } from "../../modules/projects/module";
import { settingsModule } from "../../modules/settings/module";

class ModuleRegistry {
  private readonly modules = new Map<string, MissionControlModule>();

  register(module: MissionControlModule) {
    if (this.modules.has(module.id)) {
      throw new Error(`Mission Control module already registered: ${module.id}`);
    }

    this.modules.set(module.id, module);
  }

  getModules(): MissionControlModule[] {
    return [...this.modules.values()];
  }

  getRoutes(): ModuleRoute[] {
    return this.getModules().flatMap((module) => module.routes ?? []);
  }

  getNavigationItems(): NavigationItem[] {
    return this.getModules()
      .flatMap((module) => module.navigation ?? [])
      .sort((a, b) => (a.order ?? 100) - (b.order ?? 100));
  }
}

export const moduleRegistry = new ModuleRegistry();

moduleRegistry.register(projectsModule);
moduleRegistry.register(settingsModule);