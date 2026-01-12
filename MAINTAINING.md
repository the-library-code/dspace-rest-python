# Maintenance instructions

These notes are for maintenance of the Git / PyPI source and releases / versions, rather than the installed client libraries - if you are not a maintainer, you can skip this doc!

## Release tasks

All the tasks we need to do, in order, when releasing a new version:

1. **Check the main branch!** - we should have all the changes we want to include merged/picked and tested
1. **Update CHANGELOG.md** - new versions go at the top of the file. See previous release blocks for formatting. I include a 'thanks' or 'reported by' attribution for PRs contributed or issues reported. The new version number is used for the heading and the (future) PyPI URL
1. **Update pyproject.toml dependencies** - This should match requirements.txt dependencies, and also check the rest of the metadata in case that has changed
1. **Commit release preparation** - once you are happy with the steps above, commit with a message like 'Prepare release 0.1.17'
1. **Push branch** - making sure github is up to date, (in future: CI)
1. **Tag with new version number** - this is now done with a git tag (previously required editing `__init__.py`), e.g. `git tag v0.1.17, then pushing, should now mean the build process reads that tag as the version number
1. **Clear out build and dist directories**: OPTIONAL, but nice to start with a clean Python build environment before making this new version
1. **Run local build** - `python -m build` should build `dist` and `egg-into` directories with the correct version number included
1. **Publish to PyPI** - e.g. with twine, `twine upload --repository dspace-rest-client dist/*` (you can be specific with the version build in dist/ if you have multiples. You need credentials in your ~/.pypirc)
