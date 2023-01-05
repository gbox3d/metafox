#%%
import socket
import yaml
import struct

import io
from PIL import Image, ImageDraw, ImageFont
from IPython.display import display



# %%
class veroTcpClient:
    def __init__(self,ip,port,checkcode=20221223,buff_size=1024,bankId=0,timeout=1) :
        self.ip = ip
        self.port = port
        self.buff_size = buff_size
        self.checkcode = checkcode
        self.bankId = bankId
        self.timeout = timeout
    def connect(self) :
        try :
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.ip, self.port))
            self.client_socket.settimeout(1)
            print('connected ok')
            
            _result = self.client_socket.recv(1024)
            _code,_cmd = struct.unpack('<LB', _result[:5])
            print(f'code : {_code}, cmd : {_cmd}')
            
        except Exception as ex:
            print(f'error : {ex}')
    def send_ping(self) :
        _packpack = struct.pack('<LB', self.checkcode,0x10)
        _packpack += bytearray(27) #padding
        self.client_socket.sendall(_packpack)
        
        _result = self.client_socket.recv(self.buff_size)
        _code,_cmd = struct.unpack('<LB', _result[:5])
        print(f'code : {_code}, cmd : {_cmd}')
        
    def send_data(self,data) :
        # with open('test.png', 'rb') as f:
        #     _data = f.read()
        #     _header = struct.pack('<LBBBBL', self.checkcode,0x01,0,0,0,len(_data))
        #     _header += bytearray(20) #padding 12+20 = 32
        #     self.client_socket.sendall(_header)
        #     self.client_socket.sendall(_data)
        _data = data
        _header = struct.pack('<LBBBBL', self.checkcode,0x01,self.bankId,0,0,len(_data))
        _header += bytearray(20) #padding 12+20 = 32
        self.client_socket.sendall(_header)
        self.client_socket.sendall(_data)
        
        print('send data ok')
            
        # _result = self.client_socket.recv(1024)
        # _code,_cmd,_,_,_,buff_size = struct.unpack('<LBBBBL', _result)
        # print(f'code : {_code}, cmd : {_cmd} , buff_size : {buff_size}')
        
    def download(self) :
        
        _header = struct.pack('<LBB', self.checkcode,0x02,self.bankId)
        _header += bytearray(26) #padding 12+20 = 32
        self.client_socket.sendall(_header)
        
        
        _result = self.client_socket.recv(self.buff_size)
        
        #read header
        _code,_cmd,_,_,_,buff_size = struct.unpack('<LBBBBL', _result[0:12])
        print(f'code : {_code}, cmd : {_cmd} , buff_size : {buff_size}')
        
        #read data
        _data = _result[32:]
        while len(_data) < buff_size :
            _data += self.client_socket.recv(self.buff_size)
        
        display(Image.open(io.BytesIO(_data)))
        
        
    def close(self) :
        _packpack = struct.pack('<LB', self.checkcode,0x99)
        _packpack += bytearray(27) #padding
        self.client_socket.sendall(_packpack)
        
        _result = self.client_socket.recv(self.buff_size)
        _code,_cmd = struct.unpack('<LB', _result[:5])
        print(f'code : {_code}, cmd : {_cmd}')
        self.client_socket.close()
        
#%%
if __name__ == '__main__' :
    with open('config.yaml', 'r') as f:
        
        config_data = yaml.load(f,Loader=yaml.FullLoader)
        
        print(config_data)
        server_ip = config_data['server_ip']
        port = config_data['port']
        buff_size = config_data['buff_size']
    checkcode = 20221223
    _sender = veroTcpClient(server_ip,port,checkcode,buff_size)
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
                
                with open('test.png', 'rb') as f:
                    _data = f.read()
                    _sender.send_data(_data)
                    
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