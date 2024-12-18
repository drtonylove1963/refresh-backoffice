from setuptools import setup, find_packages

setup(
    name="refresh-church-visit-planner",
    version="0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'flask',
        'flask-sqlalchemy',
        'flask-migrate',
        'flask-mail',
        'flask-login',
        'flask-wtf',
    ]
)
