# piki

Piki is a minimal wiki.


## Installation
### Get the repository
####Go to the subfolder, where you want to create your new Piki-Application (here ~/tmp)
    cd ~/tmp
#### Clone the repository
    git clone https://git.mount-mockery.de/application/piki.git
#### Change to your repository and initialise it completely
    cd piki
    git submodule init
    git submodule update


### Create your virtual environment
#### Create python3 environment
    python3 -m venv venv
#### Activate the environment
    source venv/bin/activate
#### Install PaTT Requirements
    pip install -r requirements.txt

## Configuration and Initialisation of Piki
### Create your config File
#### Copy the config example
    cp config_example/config.py .
    chmod 700 config.py

#### Set a secret key
Edit config.py and add a SECRET_KEY. Generate the secret e.g by executing the following command:

    python manage.py

At the End of the error message you'll see a random secret:

KeyError: "You need to create a config.py file including at least a SECRET_KEY definition (e.g.: --> **'HERE IS THE RANDOM SECRET ;-)'** <--)."



### Create your initial database and first user for Patt
    python manage.py migrate
    python manage.py createsuperuser

### Finalise Configuration
Now there are two ways to finalise your configuration. The first way is for a test or development system. The other is for a production System.

1. **Test or development System:** Edit config.py and set the Variable DEBUG to True.

2. **Production System:** Edit config.py and set the Variable ALLOWED_HOSTS. Execute "python manage.py collectstatic" to create a folder including all static files. Then add PaTT to your server configuration. See also [Django Documnetation](https://docs.djangoproject.com/en/3.1/howto/deployment/) for further information.

## Start the Test or development System
### Go to the folder, where your PaTT-Application is locates (here ~/tmp/piki)
    cd ~/tmp/piki

###Activate your Virtual Environment
    source activate

###Start the Server
    python manage.py runserver


## Backup
### Create Backup files
    source venv/bin/activate
    python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e sessions -e auth.Permission -e sessions -e pages --indent 2 > dump_pages.json
    tar -cvzf dump_data.tgz data/media data/pages data/media

### Restore Backup

    source venv/bin/activate

If you are starting without a database, you need to create one

    python manage.py migrate

Afterward add data step by step to the database.

    python manage.py loaddata dump_pages.json
    rm -rf data/pages data/media
    tar -xvzf dump_data.tgz
