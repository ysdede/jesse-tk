## Jesse Toolkit

### Installation
You need to install the legacy version of the jesse.

#### Linux:  
Use: [jesse stack installer](https://github.com/ysdede/stack-installer/blob/master/ubuntu-20.04.sh)

it will install modified version of legacy jesse cli.
```console
bash <(curl -s https://raw.githubusercontent.com/ysdede/stack-installer/master/jesse-cli-ubuntu20.sh)
```

then clone this repository and install with pip.

```console
pip install .
```
or
```console
pip install -e git+https://github.com/ysdede/jesse-tk.git#egg=jesse-tk
```

#### Windows:
  Download and install prebuilt ta-lib from [https://www.lfd.uci.edu/~gohlke/pythonlibs/](https://www.lfd.uci.edu/~gohlke/pythonlibs/)

  ```console
    pip install downloaded wheel file
 ```

install legacy jesse cli from [https://github.com/ysdede/jesse](https://github.com/ysdede/jesse)

Clone this repository and install with pip.
```console
pip install .
```
or
```console
pip install -e git+https://github.com/ysdede/jesse-tk.git#egg=jesse-tk
```

see old tool [jesse-picker](https://github.com/ysdede/jesse-picker) for details.




## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
[MIT](https://choosealicense.com/licenses/mit/)
