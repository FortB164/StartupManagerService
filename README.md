# Startup Manager Service

Have you ever wondered why your PC is so slow when you first boot it? Are you sick of the pesky startup apps hogging your RAM? Look no further! This is a service that manually manages all of your startup apps. It first disables them and then starts them up one at a time, making sure each one only starts once the previous one is fully running. Apps are queued and prioritized based on hardware usage, ensuring smoother startup performance and better resource management.

## Features
- **Manual App Management**: Disables all startup applications initially and only starts them one by one.
- **Sequential Startup**: Ensures that each application is fully running before the next starts.
- **Priority-Based Queueing**: Applications are queued and prioritized based on their resource usage, ensuring the most critical ones start first.
- **Improved Boot Time**: By delaying startup apps and managing their order, the system boots faster and consumes fewer resources.

## Why You Need It
When you boot up your system, all startup apps try to load at once, hogging your CPU and RAM. By manually managing and delaying the startup of these apps, your system has more resources available for essential tasks, leading to faster boot times and a smoother overall experience.

## Installation

### For Python
- ***Ensure you have Python installed and it is not from the Microsoft Store.
- ***Ensure you have pip installed.
- ***Run setup.bat to install and run.
- ***Run delete.bat to delete.


1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/startup-manager-service.git
