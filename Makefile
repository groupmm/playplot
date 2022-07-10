build:
	@(cd sphinx && make github)
	@python -m build --sdist
	@python -m build --wheel
	@twine check dist/*

publish:
	@make build
	@twine upload --repository testpypi dist/*

install:
	@make build
	@pip uninstall -y make-plot-playable
	@pip install --no-index --find-links dist/ make-plot-playable

.PHONY: build publish