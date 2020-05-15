import os
import sys
sys.path.append('./')
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.clock import mainthread
from kivy.utils import platform
import threading
import sys
if platform == 'android':
    from usb4a import usb
    from usbserial4a import serial4a
else:
    from serial.tools import list_ports
    from serial import Serial

kv = '''
BoxLayout:
    id: box_root
    orientation: 'vertical'
    
    Label:
        size_hint_y: None
        height: '50dp'
        text: 'SerialTools'
    
    ScreenManager:
        id: sm
        on_parent: app.uiDict['sm'] = self
        Screen:
            name: 'screen_menu'
            on_parent: app.uiDict['screen_menu'] = self
            BoxLayout:
                orientation: 'vertical'
                BoxLayout:
                    Button:
                        size_hint: 0.3,.1
                        text: 'Serial'
                        on_press:
                            app.uiDict['screen_menu'].manager.transition.direction = 'right'
                            app.uiDict['screen_menu'].manager.current = 'screen_serial'
                    Button:
                        size_hint: 0.3,.1
                        text: 'Show'
                        on_press:
                            app.uiDict['screen_menu'].manager.transition.direction = 'up'
                            app.uiDict['screen_menu'].manager.current = 'screen_show'
                    Button:
                        size_hint: 0.3,.1
                        text: 'Control'
                        on_press:
                            app.uiDict['screen_menu'].manager.transition.direction = 'left'
                            app.uiDict['screen_menu'].manager.current = 'screen_control'
    
        Screen:
            name: 'screen_show'
            on_parent: app.uiDict['screen_show'] = self
            BoxLayout:
                orientation: 'vertical'
                ScrollView:
                    size_hint_y: None
                    height: '50dp'
                    TextInput:
                        id: txtInput_write
                        on_parent: app.uiDict['txtInput_write'] = self
                        size_hint_y: None
                        height: max(self.minimum_height, self.parent.height)
                        text: ''
                Button:
                    id: btn_write
                    on_parent: app.uiDict['btn_write'] = self
                    size_hint_y: None
                    height: '50dp'
                    text: 'Write'
                    on_release: app.on_btn_write_release()
                ScrollView:
                    TextInput:
                        id: txtInput_read
                        on_parent: app.uiDict['txtInput_read'] = self
                        size_hint_y: None
                        height: max(self.minimum_height, self.parent.height)
                        readonly: True
                        text: ''
                Button:
                    text: 'Back to menu'
                    size_hint:  1,.1
                    on_press:
                        app.uiDict['screen_show'].manager.transition.direction = 'down'
                        app.uiDict['screen_show'].manager.current = 'screen_menu'
                
        Screen:
            name: 'screen_serial'
            on_parent: app.uiDict['screen_serial'] = self
            BoxLayout:
                orientation: 'vertical'
                BoxLayout:
                    spacing: 10
                    size_hint: 1,.3
                    Spinner:
                        text: 'COM'
                        on_parent: app.uiDict['Spinner_com'] = self
                        size_hint_x: .3
                        size_hint_y: None
                        height: '50dp'     
                        on_release: app.on_btn_scan_release()
                    Spinner:
                        text: 'Baudrate'
                        on_parent: app.uiDict['Spinner_baudrate'] = self
                        size_hint_x: .3
                        size_hint_y: None
                        height: '50dp'     
                        values: '9600', '14400','57600','115200'
            
                    Button:
                        text: 'connect'
                        on_parent: app.uiDict['btn_connect'] = self              
                        size_hint_x: .3
                        size_hint_y: None
                        height: '50dp'                        
                        on_press: app.on_btn_device_release()
                Button:
                    text: 'Back to menu'
                    size_hint_y: None
                    height: '50dp'
                    on_press:
                        app.uiDict['screen_serial'].manager.transition.direction = 'left'
                        app.uiDict['screen_serial'].manager.current = 'screen_menu'
        Screen:
            name: 'screen_control'
            on_parent: app.uiDict['screen_control'] = self
            BoxLayout:
                orientation: 'vertical'
                Button:
                    text: 'Back to menu'
                    size_hint:  1,.1
                    on_press:
                        app.uiDict['screen_control'].manager.transition.direction = 'right'
                        app.uiDict['screen_control'].manager.current = 'screen_menu'
'''


class MainApp(App):
    def __init__(self, *args, **kwargs):
        self.uiDict = {}
        self.device_name_list = []
        self.serial_port = None
        self.read_thread = None
        self.port_thread_lock = threading.Lock()
        super(MainApp, self).__init__(*args, **kwargs)

    def build(self):
        return Builder.load_string(kv)

    def on_stop(self):
        if self.serial_port:
            with self.port_thread_lock:
                self.serial_port.close()
        self.uiDict['btn_connect'].text = 'connect'
        self.serial_port = None
        self.read_thread = None

    def on_btn_scan_release(self):
        self.device_name_list = []
        if platform == 'android':
            usb_device_list = usb.get_usb_device_list()
            self.device_name_list = [
                device.getDeviceName() for device in usb_device_list
            ]
        else:
            usb_device_list = list_ports.comports()
            self.device_name_list = [port.device for port in usb_device_list]

        self.uiDict['Spinner_com'].values = self.device_name_list

    def on_btn_device_release(self):
        if self.uiDict['btn_connect'].text == 'disconnect':
            self.on_stop()
            return
        device_name = self.uiDict['Spinner_com'].text
        device_baudrate = self.uiDict['Spinner_baudrate'].text

        try:
            if platform == 'android':
                device = usb.get_usb_device(device_name)
                if not device:
                    return
                if not usb.has_usb_permission(device):
                    usb.request_usb_permission(device)
                    return
                self.serial_port = serial4a.get_serial_port(
                    device_name,
                    device_baudrate,
                    8,
                    'N',
                    1,
                    timeout=1
                )
            else:
                self.serial_port = Serial(
                    device_name,
                    device_baudrate,
                    8,
                    'N',
                    1,
                    timeout=1
                )
        except Exception as e:
            return
        if self.serial_port.is_open and not self.read_thread:
            self.read_thread = threading.Thread(target=self.read_msg_thread)
            self.read_thread.start()
            self.uiDict['btn_connect'].text = 'disconnect'

        self.uiDict['sm'].current = 'screen_show'

    def on_btn_write_release(self):
        if self.serial_port and self.serial_port.is_open:
            if sys.version_info < (3, 0):
                data = bytes(self.uiDict['txtInput_write'].text + '\n')
            else:
                data = bytes(
                    (self.uiDict['txtInput_write'].text + '\n'),
                    'utf8'
                )
            self.serial_port.write(data)
            self.uiDict['txtInput_read'].text += '[Sent]{}\n'.format(
                self.uiDict['txtInput_write'].text
            )
            self.uiDict['txtInput_write'].text = ''

    def read_msg_thread(self):
        while True:
            try:
                with self.port_thread_lock:
                    if not self.serial_port.is_open:
                        break
                    received_msg = self.serial_port.read(
                        self.serial_port.in_waiting
                    )
                if received_msg:
                    msg = bytes(received_msg).decode('utf8')
                    self.display_received_msg(msg)
            except Exception as ex:
                break

    @mainthread
    def display_received_msg(self, msg):
        self.uiDict['txtInput_read'].text += msg
        if sys.getsizeof(self.uiDict['txtInput_read'].text) > 2000:
            self.uiDict['txtInput_read'].text = ''


if __name__ == '__main__':
    MainApp().run()
