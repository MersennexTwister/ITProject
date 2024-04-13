#!/usr/bin/bash

echo Installing libs...

apt install git apache2 libapache2-mod-wsgi-py3 libgl1-mesa-glx python3 python3-pip
systemctl restart apache2
systemctl enable apache2
a2enmod wsgi

echo Clonning repo...

export PROJECT_DIR="/opt/project-mars"
git clone https://github.com/MersennexTwister/project-mars $PROJECT_DIR
chown -R :www-data $PROJECT_DIR
chmod -R 775 $PROJECT_DIR

echo Cloned successfully!
echo Preparing data...

mkdir $PROJECT_DIR/encs $PROJECT_DIR/site_image_cache $PROJECT_DIR/static/undefined_image_cache

echo finished!
echo Installing python requirements...

wget -O /tmp/dlib.tar.gz "https://files.pythonhosted.org/packages/af/a4/226dbb659e913a4a149b35980e87e10050ea39a0dceac934e9e73cccbef1/dlib-19.24.4.tar.gz#sha256=f83dfdf6e85b91fc2b54ea5aad7932a5617cd61e9d13fc72055e22c7d9e264ff"
tar -zxvf /tmp/dlib.tar.gz -C /tmp
cd /tmp/dlib-19.24.4
python3 /tmp/dlib-19.24.4/setup.py install
pip install -r $PROJECT_DIR/requirements.txt

echo Requirements installed successfully!
echo Apache2 setup...

touch /etc/apache2/sites-available/mars.conf
cat $PROJECT_DIR/mars.conf > /etc/apache2/sites-available/mars.conf
cat Listen 8000 >> /etc/apache2/ports.conf
a2ensite mars
systemctl restart apache2

echo Installation complete!
