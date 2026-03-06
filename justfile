default: lint

pdf-docs: latex-docs
	make -C doc-source/build/latex/

latex-docs:
	SPHINX_BUILDER=latex tox -e docs

unused-imports:
	tox -e lint -- --select F401

incomplete-defs:
	tox -e lint -- --select MAN

commas:
	tox -e lint -- --select C810,C812,C813,C814,C815,C816

vdiff:
	git diff $(repo-helper show version -q)..HEAD

bare-ignore:
	greppy '# type:? *ignore(?!\[|\w)' -s

lint: unused-imports incomplete-defs bare-ignore myts
	tox -n qa

tsc:
	- npx tsc
	- pre-commit run eslint --files folium_zoom_state/*.js
	- just --justfile "{{justfile()}}" clean-js

myts:
	npx tsc --noEmit -p tsconfig.json

clean-js:
	- pre-commit run trailing-whitespace --files folium_zoom_state/*.js
	- pre-commit run end-of-file-fixer --files folium_zoom_state/*.js
	- pre-commit run remove-crlf --files folium_zoom_state/*.js

build: tsc
	tox -e build

licence-report:
	npx license-report --only=prod --output html > licence-report.html

swc:
	swc compile src/zoom_state.ts --out-file folium_zoom_state/zoom_state.js
