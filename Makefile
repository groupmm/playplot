build:
	@(cd sphinx && make github)
	@python -m build --sdist
	@python -m build --wheel
	@twine check dist/*

publish:
	@make build
	@twine upload dist/*

test-publish:
	@make build
	@twine upload --repository testpypi dist/*

dev-install:
	@pip uninstall -y playplot
	@pip install -e .

install:
	@make build
	@pip uninstall -y playplot
	@pip install --no-index --find-links dist/ playplot

.PHONY: build publish