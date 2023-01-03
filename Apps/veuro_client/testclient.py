#%%
import socket
import yaml
import struct

import io
from PIL import Image, ImageDraw, ImageFont
from IPython.display import display


checkcode = 20221223

#%%
with open('config.yaml', 'r') as f:
        
    config_data = yaml.load(f,Loader=yaml.FullLoader)
    
    print(config_data)
    server_ip = config_data['server_ip']
    port = config_data['port']
    buff_size = config_data['buff_size']


# %%
class veroTestClient:
    def __init__(self,ip,port,buff_size) :
        self.ip = ip
        self.port = port
        self.buff_size = buff_size
    def connect(self) :
        try :
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.ip, self.port))
            self.client_socket.settimeout(1)
            print('connected ok')
            
            _result = self.client_socket.recv(1024)
            _code,_cmd,_,_,_ = struct.unpack('<LBBBB', _result)
            print(f'code : {_code}, cmd : {_cmd}')
            
            
        except Exception as ex:
            print(f'error : {ex}')
    def send_ping(self) :
        _packpack = struct.pack('<LBBBB', checkcode,0x10,0,0,0)
        self.client_socket.sendall(_packpack)
        _result = self.client_socket.recv(1024)
        _code,_cmd,_,_,_ = struct.unpack('<LBBBB', _result)
        print(f'code : {_code}, cmd : {_cmd}')
    def send_data(self) :
        with open('test.png', 'rb') as f:
            _data = f.read()
            _header = struct.pack('<LBBBBLffLLL', checkcode,0x01,0,0,0,len(_data),0,0,0,0,0)
            self.client_socket.sendall(_header)
            self.client_socket.sendall(_data)
            
        _result = self.client_socket.recv(1024)
        _code,_cmd,_,_,_,buff_size = struct.unpack('<LBBBBL', _result)
        
        print(f'code : {_code}, cmd : {_cmd} , buff_size : {buff_size}')
    def download(self) :
        
        _header = struct.pack('<LBBBB', checkcode,0x02,0,0,0)
        self.client_socket.sendall(_header)
        
        _result = self.client_socket.recv(1024)
        
        #read header
        _code,_cmd,_,_,_,buff_size = struct.unpack('<LBBBBL', _result[0:12])
        print(f'code : {_code}, cmd : {_cmd} , buff_size : {buff_size}')
        
        #read data
        _data = _result[12:]
        while len(_data) < buff_size :
            _data += self.client_socket.recv(1024)
        
        display(Image.open(io.BytesIO(_data)))
        
        
    def close(self) :
        _packpack = struct.pack('<LBBBB', checkcode,0x99,0,0,0)
        self.client_socket.sendall(_packpack)
        _result = self.client_socket.recv(1024)
        _code,_cmd,_,_,_ = struct.unpack('<LBBBB', _result)
        print(f'code : {_code}, cmd : {_cmd}')
        self.client_socket.close()
        
#%%
if __name__ == '__main__' :
    _sender = veroTestClient(server_ip,port,buff_size)
    while True :
        _cmd = input('cmd : ')
        try :
            if _cmd == 'ping' :
                _sender.send_ping()
            elif _cmd == 'connect' :
                _sender.connect()
            elif _cmd == 'close' :
                _sender.close()
                break
            elif _cmd == 'test1' :
                _sender.connect()
                _sender.send_ping()
                _sender.send_data()
                _sender.close()
            elif _cmd == 'test2' :
                _sender.connect()
                _sender.send_ping()
                _sender.download()
                _sender.close()

            elif _cmd == 'exit' :
                break
            print(f'{_cmd} command ok')
        except Exception as ex :
            print(f'error : {ex}')
        
# %%