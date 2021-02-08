from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()
long_description = (here / 'README.md').read_text(encoding='utf-8')

setup(name='ratpy',
      version = '1.0.0.dev3',
      description = 'An interpreter and visualiser of RATS files',
      author = 'Steve Ayrton',
      author_email = 's.t.ayrton@icloud.com',
      licence='MIT',
      classifiers=[  # Optional
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7'
    ],

      packages=find_packages(),
      install_requires=['pandas','dash','plotly_express','plotly','numpy','dash_bootstrap_components','beautifulsoup4','pyarrow','dash-uploader'],
      python_requires='>=3.6'

)



