
from setuptools import setup, find_packages

# FIXME: come up with a better name
setup(name='dedup',
      maintainer='David Wallin',
      maintainer_email='dedup@datawrangler.ninja',
      description='Deduplication Tool',

      #url='https://SOMETHING/SOMETHING/sampling',

      setup_requires=['setuptools-git-versioning',
                      'setuptools_git'],

      version_config=True,

      packages=find_packages(),
      include_package_data=True,

      install_requires=[
          'Click',
          'click-log',
          'click-help-colors',
          'humanfriendly',
          'pandas',
          'tabulate'
      ],
      extras_require={'extra_hash': ['blake3',
                                     'xxhash']}
      # entry_points='''
      #   [console_scripts]
      #   s=cli:ensure_net
      # ''',
)
