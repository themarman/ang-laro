# Setting up an Xbox Controller in WSL

To use a USB controller (like an Xbox controller) with this game running in WSL, you need to "bridge" the connection from Windows to Linux. By default, Linux cannot see devices plugged into your Windows computer.

## Prerequisites
1.  **Windows 11** (or Windows 10 with latest updates).
2.  **Administrator Access** to your Windows computer.

## Step 1: Install `usbipd-win` on Windows
1.  Open a **Windows PowerShell** or **Command Prompt** as **Administrator**.
2.  Run the following command to install the USB Bridge tool:
    ```powershell
    winget install usbipd
    ```
3.  After installation, close and reopen the Admin terminal.

## Step 2: Identify your Controller
1.  Ensure your Xbox controller is plugged in via USB.
2.  In the **Windows Admin Terminal**, run:
    ```powershell
    usbipd list
    ```
3.  Look for a device named **"Controller"** or **"Xbox Gaming Device"**. Note its **BUSID** (e.g., `2-4`).

## Step 3: Attach the Controller to WSL
1.  Run the following command in the **Windows Admin Terminal** (replace `<BUSID>` with your ID):
    ```powershell
    usbipd bind --busid <BUSID>
    usbipd attach --wsl --busid <BUSID>
    ```
2.  You should see a message confirming the device is attached.

## Step 4: Verify in Linux
1.  Return to this terminal (the IDE/Linux one).
2.  Run the debug script again:
    ```bash
    source .venv/bin/activate
    python debug_controller.py
    ```
3.  It should now detect "1 joystick".

## Troubleshooting
*   **"Access Denied":** Make sure you are running the Windows terminal as Administrator.
*   **Device Disconnects:** If you unplug the controller, you must re-run the `attach` command (Step 3) when you plug it back in.
