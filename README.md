<h1 align="center"><a href="http://olliefgl.pythonanywhere.com/"/>Fantasy Gambling League</a></h1>
</br></br>

<p align="center">
    <a href="https://circleci.com/gh/ollie-codeaid/fgl" alt="CircleCI">
        <img src="https://circleci.com/gh/ollie-codeaid/fgl.svg?style=shield&circle-token=005e841397d5dee7e434165b34691b77cae3c30c" /></a>
    <a href="https://codecov.io/gh/ollie-codeaid/fgl" alt="Codecov">
        <img src="https://codecov.io/gh/ollie-codeaid/fgl/badge.svg" /></a>
</p>


## Local development

```bash
pyenv install 2.7.18
pyenv local 2.7.18
pyenv virtualenv fgl
pyenv activate fgl
pip install -r requirements.txt
export DJANGO_SETTINGS_MODULE=fglsite.settings.dev
python manage.py runserver
```
