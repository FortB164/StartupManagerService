import os
import json
import time
import psutil
import winreg
import logging
import subprocess
from win32serviceutil import ServiceFramework, HandleCommandLine
from win32service import SERVICE_STOPPED, SERVICE_RUNNING

class StartupApp:
    def __init__(self, name, path, cpu_usage=0, memory_usage=0, dependencies=None):
        self.name = name
        self.path = path
        self.cpu_usage = cpu_usage
        self.memory_usage = memory_usage
        self.dependencies = dependencies if dependencies else []

    def to_dict(self):
        return {
            "Name": self.name,
            "Path": self.path,
            "CpuUsage": self.cpu_usage,
            "MemoryUsage": self.memory_usage,
            "Dependencies": self.dependencies
        }

class StartupManagerService(ServiceFramework):
    _svc_name_ = "StartupManagerService"
    _svc_display_name_ = "Startup Manager Service"

    CONFIG_DIR = os.path.join(os.getenv("APPDATA"), "StartupManager")
    CONFIG_FILE = os.path.join(CONFIG_DIR, "startup_apps.json")
    LOG_FILE = os.path.join(CONFIG_DIR, "service.log")

    def __init__(self, args):
        ServiceFramework.__init__(self, args)
        self.startup_apps = []
        if not os.path.exists(self.CONFIG_DIR):
            os.makedirs(self.CONFIG_DIR)
        logging.basicConfig(filename=self.LOG_FILE, level=logging.INFO, format='%(asctime)s %(message)s')

    def SvcStop(self):
        self.ReportServiceStatus(SERVICE_STOPPED)
        logging.info("Service stopped.")

    def SvcDoRun(self):
        self.ReportServiceStatus(SERVICE_RUNNING)
        logging.info("Service started.")
        self.manage_startup()

    def manage_startup(self):
        try:
            self.detect_and_disable_startup_apps()
            self.measure_resource_usage()
            self.execute_startup_apps_in_priority_order()
        except Exception as e:
            logging.error(f"Error in manage_startup: {e}")

    def detect_and_disable_startup_apps(self):
        previous_apps = self.load_previous_startup_apps()
        current_apps = self.get_startup_apps()
        new_apps = []
        
        for app in current_apps:
            previous_app = next((p for p in previous_apps if p.name == app.name), None)
            if "StartupManagerService.exe" in app.path:
                logging.info(f"Skipping self-exclusion for {app.name}")
                continue

            if not previous_app or (previous_app and previous_app.cpu_usage == 0 and previous_app.memory_usage == 0):
                self.disable_app_in_registry(app.name)
                new_apps.append(app)

        all_apps = previous_apps + new_apps
        with open(self.CONFIG_FILE, "w") as f:
            json.dump([app.to_dict() for app in all_apps], f, indent=4)
        logging.info("Startup apps detected, disabled where needed, and stored.")

    def load_previous_startup_apps(self):
        if os.path.exists(self.CONFIG_FILE):
            with open(self.CONFIG_FILE, "r") as f:
                data = json.load(f)
                return [StartupApp(**app) for app in data]
        return []

    def get_apps_from_registry(self, hive, subkey):
        apps = []
        try:
            with winreg.OpenKey(hive, subkey) as key:
                i = 0
                while True:
                    try:
                        value_name, value_data, _ = winreg.EnumValue(key, i)
                        apps.append(StartupApp(name=value_name, path=value_data))
                        i += 1
                    except OSError:
                        break
        except FileNotFoundError:
            logging.error(f"Registry key not found: {subkey}")
        return apps

    def get_startup_apps(self):
        apps = self.get_apps_from_registry(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run")
        apps += self.get_apps_from_registry(winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run")
        return apps

    def disable_app_in_registry(self, app_name):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, app_name, 0, winreg.REG_BINARY, b"\x03")
            winreg.CloseKey(key)
        except Exception as e:
            logging.error(f"Error in disable_app_in_registry: {e}")

    def measure_resource_usage(self):
        for app in self.startup_apps:
            try:
                proc = subprocess.Popen(app.path)
                time.sleep(5)
                cpu = psutil.Process(proc.pid).cpu_percent(interval=1)
                memory = psutil.Process(proc.pid).memory_info().rss / (1024 * 1024)
                app.cpu_usage = cpu
                app.memory_usage = memory
                proc.kill()
            except Exception as e:
                logging.error(f"Error measuring resource usage for {app.name}: {e}")
        with open(self.CONFIG_FILE, "w") as f:
            json.dump([app.to_dict() for app in self.startup_apps], f, indent=4)

    def execute_startup_apps_in_priority_order(self):
        self.startup_apps.sort(key=lambda x: x.cpu_usage + x.memory_usage)
        started_apps = set()
        for app in self.startup_apps:
            if all(dep in started_apps for dep in app.dependencies):
                subprocess.Popen(app.path)
                started_apps.add(app.name)
                logging.info(f"Started {app.name} successfully.")

if __name__ == '__main__':
    HandleCommandLine(StartupManagerService)
