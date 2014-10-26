from setuptools import setup, find_packages

setup(
    name="django-notification-automated",
    description="User notification management for the Django web framework",
    long_description=open("docs/usage.txt").read(),
    url="https://github.com/arctelix/django-notification-automated",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Framework :: Django",
    ],
    include_package_data=True,
    zip_safe=False,
)
