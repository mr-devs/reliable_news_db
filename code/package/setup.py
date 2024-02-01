from setuptools import setup

# tests_require = [
#     "vcrpy>=1.10.3",
# ]

setup(
    name="reliable_db",
    version="0.1",
    description="Local package for generating the reliable news database.",
    license="MIT",
    author="Matthew DeVerna",
    packages=["reliable_db"],
    # install_requires=[
    #     "requests>=2.24.0",
    #     "requests_oauthlib>=1.3.0"
    # ],
    # tests_require=tests_require,
    python_requires=">=3.9",
)
