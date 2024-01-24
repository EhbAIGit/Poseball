# Poseball
Move a Sphero Bolt with your body gestures

1. On your Ubuntu, download and install Anaconda
    
    ```bash
    cd ../Downloads/
    
    bash Anaconda3-2023.07-2-Linux-x86_64.sh
    
    conda –version
    ```
    
2. Create a Python environment
    
    ```python
    conda create --name sphero310 python=3.10
    
    conda activate sphero310
    ```
    
3. Install prerequisite packages
    
    ```bash
    sudo apt-get update
    sudo apt-get upgrade
    # Development package for the GLib library -- prerequisite for bluepy
    sudo apt install libglib2.0-dev
    # Development package for D-Bus, a message bus system used for interprocess communication on Linux -- prerequisite for dbus-python
    sudo apt install libdbus-1-dev
    # Bluetooth management on Linux 
    sudo apt install bluez-tools
    
    sudo apt-get install socket
    ```
    
4. Install all dependencies
    
    ```bash
    pip install bleak
    pip install bluepy
    pip install gatt
    pip install pygatt
    pip install pysphero
    pip install dbus-python
    pip install numpy
    pip install spherov2
    
    pip install opencv-python
    pip install mediapipe
    
    ```
    
5. Verify that blue tooth is getting detected:
    
    ```bash
    bt-device -l
    ```
    
6. Create python file with following code:
    
    [sphero2.py](https://prod-files-secure.s3.us-west-2.amazonaws.com/9e720eef-740b-45c1-af9d-0bc4c4d0ac81/0a3bb51d-ac89-4b0b-8f95-d881f2b72ef3/sphero2.py)
    
    ```python
    import time
    from spherov2 import scanner
    from spherov2.sphero_edu import SpheroEduAPI
    from spherov2.types import Color
    
    class SpheroController:
        def __init__(self):
            self.toy = None
    
        def discover_toy(self):
            try:
                self.toy = scanner.find_toy()
            except Exception as e:
                print(f"Error discovering toy: {e}")
    
        def connect_toy(self):
            if self.toy is not None:
                try:
                    return SpheroEduAPI(self.toy)
                except Exception as e:
                    print(f"Error connecting to toy: {e}")
            else:
                print("No toy discovered. Please run discover_toy() first.")
    
        def run(self):
            self.discover_toy()
            with self.connect_toy() as api:
                if api is not None:
                    try:
                        api.set_main_led(Color(r=0, g=0, b=255))
                        api.set_speed(60)
                        time.sleep(2)
                        api.set_speed(0)
                    except Exception as e:
                        print(f"Error: {e}")
    
    def main():
        controller = SpheroController()
        controller.run()
    
    if __name__ == "__main__":
        main()
    ```
    
7. Run the file and the Sphero Bolt will be connected.
