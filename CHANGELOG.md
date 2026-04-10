# Changelog

## [0.5.0](https://github.com/wtewalt/timeo/compare/v0.4.0...v0.5.0) (2026-04-10)


### Features

* improve learn-mode timing accuracy with decaying alpha, drift detection, and depends_on ([10d8fda](https://github.com/wtewalt/timeo/commit/10d8fda2ffb366933609307f51fe2602a0154a65))


### Documentation

* add GitHub repository badge to README header ([ff50b2f](https://github.com/wtewalt/timeo/commit/ff50b2feca03df7ed024dcab866c808f571ceeb2))
* document decaying alpha, drift detection, and depends_on in README and CLAUDE.md ([593343e](https://github.com/wtewalt/timeo/commit/593343e7973095ffa39453a9ff5c53cc70d60bd7))

## [0.4.0](https://github.com/wtewalt/timeo/compare/v0.3.0...v0.4.0) (2026-04-10)


### Features

* add --before date filter to cache reset command ([389915a](https://github.com/wtewalt/timeo/commit/389915ac9df1da6d40692d3b5765b3479e5bfb37))
* add CLI for cache inspection and reset ([380eaf2](https://github.com/wtewalt/timeo/commit/380eaf2a729b0aa8b14eab1daf93af18916d6164))


### Documentation

* add CLI cache inspection commands to CONVENTIONS.md testing section ([cfe2788](https://github.com/wtewalt/timeo/commit/cfe2788c061d46e3e59cadce424931ae263c16ee))
* update CLAUDE.md with accurate hooks, project structure, release trigger, and cache API ([43e3cf1](https://github.com/wtewalt/timeo/commit/43e3cf1bccc5aaca2f843f42eb8b064ac11cc233))

## [0.3.0](https://github.com/wtewalt/timeo/compare/v0.2.1...v0.3.0) (2026-04-09)


### Features

* add configurable cache location to [@timeo](https://github.com/timeo).track ([4c0f0d2](https://github.com/wtewalt/timeo/commit/4c0f0d2be1fcae81c1095315e3b5842be951e3a7))
* add configurable cache location to [@timeo](https://github.com/timeo).track ([679a9eb](https://github.com/wtewalt/timeo/commit/679a9eb654b18c22df0ca2613dd881cbad95a24e))

## [0.2.1](https://github.com/wtewalt/timeo/compare/v0.2.0...v0.2.1) (2026-04-09)


### Documentation

* remove contributing section, restore dynamic PyPI version badge ([5ba39d7](https://github.com/wtewalt/timeo/commit/5ba39d764371246dc3191435d54f6be18d6ab5af))

## [0.2.0](https://github.com/wtewalt/timeo/compare/v0.1.0...v0.2.0) (2026-04-09)


### Features

* add smoke test scripts for sequential, concurrent, and live con… ([92f52a8](https://github.com/wtewalt/timeo/commit/92f52a8f7d5a658afd17d9df0abb33ef95f479f7))
* add smoke test scripts for sequential, concurrent, and live context modes ([6f14c94](https://github.com/wtewalt/timeo/commit/6f14c94cc424ea4afd1885f674e21e395b5e3007))
* add test suite for task, hashing, cache, decorator, and learn mode ([754fd86](https://github.com/wtewalt/timeo/commit/754fd86a95280c2e7312ba0a02cb79162531d2aa))
* implement [@timeo](https://github.com/timeo).track decorator, advance(), and iter() ([8894dbf](https://github.com/wtewalt/timeo/commit/8894dbfe853b4e57ef35a4fed97202f4a07107d5))
* implement learn mode (learn=True) with EMA-driven progress bar ([946ea49](https://github.com/wtewalt/timeo/commit/946ea49b60fe3d512cf4a10f0922193b3479d9cc))
* implement learn mode (learn=True) with EMA-driven progress bar ([dda6553](https://github.com/wtewalt/timeo/commit/dda6553476345e62bea4dda0943e6392c14b0fda))
* implement ProgressManager singleton ([d352bb8](https://github.com/wtewalt/timeo/commit/d352bb87be0baddae592e02359bc90e8456c22d2))
* implement ProgressManager singleton ([83a9151](https://github.com/wtewalt/timeo/commit/83a91510eb4643f4ab7a0e78bfe4d7463af18fec))
* implement timing cache and function bytecode hashing ([9bf46fb](https://github.com/wtewalt/timeo/commit/9bf46fb491da12e616f9a5582fe5f3ee91d24012))
* implement timing cache and function bytecode hashing ([7942968](https://github.com/wtewalt/timeo/commit/7942968c7bbb73b5cd290af1b4258677d9550192))
* implement TrackedTask model ([b7421e3](https://github.com/wtewalt/timeo/commit/b7421e39146bbfdfcf3a9997a86341486cf8f994))
* scaffold timeo package structure ([fd042bb](https://github.com/wtewalt/timeo/commit/fd042bbb2f2e5e5c0ffca2d2affa9d09875b6cfe))


### Bug Fixes

* add future annotations import to task.py for Python 3.9 compat ([6fc84f3](https://github.com/wtewalt/timeo/commit/6fc84f318a5ab8c7ea58bbc608eb308e5832ac39))
* add future annotations import to task.py for Python 3.9 compat ([e365cf7](https://github.com/wtewalt/timeo/commit/e365cf793dde69fd8faf8aae6c3a640e2a970225))
* restore ProgressManager implementation on feat/track-decorator branch ([7366fc7](https://github.com/wtewalt/timeo/commit/7366fc7f823f9f890f8a50f3c26301a1b63e3ebc))
* updated script for initial test ([a02281d](https://github.com/wtewalt/timeo/commit/a02281de1bb0766b0d42d8cbeab4212a8ab11776))
* use endswith for qualname assertion in learn mode test ([893dda8](https://github.com/wtewalt/timeo/commit/893dda81955ba21af89fc91d318dac303b7673cb))


### Documentation

* add CLAUDE.md with project overview and architecture ([369a524](https://github.com/wtewalt/timeo/commit/369a524e7f39c620018b337653b06c6d9b5bc267))
* add CONVENTIONS.md with commit, branch, pre-commit, and release standards ([2cdb283](https://github.com/wtewalt/timeo/commit/2cdb283ce5b0ca844eaaa6426973cf762e553ddf))
* add nix shell requirement to development environment section ([7a2b2ec](https://github.com/wtewalt/timeo/commit/7a2b2ec825e755c0490d1bfe7508fc2a5f90e7dc))
* add stepwise development plan in steps/ ([300f3b8](https://github.com/wtewalt/timeo/commit/300f3b8f2ca8964455c37285dee161af997a33cf))
* add timing-based progress estimation design to CLAUDE.md ([d6bcb9b](https://github.com/wtewalt/timeo/commit/d6bcb9bcd5c6ac891c55bd8a950b33720f5f8d84))
* document release-please, PyPI publishing, and pre-commit setup ([7d82fad](https://github.com/wtewalt/timeo/commit/7d82fad72d1682cf1aab0bfd54d14d001906e507))
* redesign README with badges, tables, and improved formatting ([bdb3f3f](https://github.com/wtewalt/timeo/commit/bdb3f3f22b644847c7423d68a6218276d01600be))
* resolve all open design questions in CLAUDE.md ([7acf12a](https://github.com/wtewalt/timeo/commit/7acf12a0861a29cb54f23cce5196b1ba4c7ec033))
* write README with usage examples for basic, learn, and concurrent modes ([87201b5](https://github.com/wtewalt/timeo/commit/87201b5abfa65d905e9b21f426df99a6ff38e35d))

## 0.1.0 (2026-04-03)


### Features

* added rich as a dependency ([262c826](https://github.com/wtewalt/timeo/commit/262c826123b46339d83457578962f8a3e08e2cf1))
* change to release config ([094f8ea](https://github.com/wtewalt/timeo/commit/094f8ea74b23f885fdfb4e9dd0b6ea10a53d6cdd))
* enabled pre-commit checks and release tracking ([4ab1608](https://github.com/wtewalt/timeo/commit/4ab160830194534141c411777242a81f188294eb))
* flake added ([826aac3](https://github.com/wtewalt/timeo/commit/826aac3f67c76fbff8bb85fb1db9f570db22929d))
* new flake ([0f0b1f9](https://github.com/wtewalt/timeo/commit/0f0b1f93b4da0cb7c1d8a0eef50ef48175756de2))
* new nix config ([858f3ff](https://github.com/wtewalt/timeo/commit/858f3ff2d2af71f401c9b769ff871487e3f37042))
* updates to release ([1690435](https://github.com/wtewalt/timeo/commit/1690435928b06eeff239a49b448a80aaed3b580f))
* working flake with uv and pre-commit hooks ([c49b388](https://github.com/wtewalt/timeo/commit/c49b3888c56d8386b07445c39aa1b849e2abaaad))


### Bug Fixes

* added changelog ([59d9c6f](https://github.com/wtewalt/timeo/commit/59d9c6f138d6bd8299a8e8cf87b9d3b1f6a87d54))
* updates to allow release tracking ([76fa10f](https://github.com/wtewalt/timeo/commit/76fa10f46d56eb37b5b821edce96946b4b3e3dda))
