FROM nousresearch/hermes-agent:latest
COPY . /opt/personal-expense
RUN /opt/hermes/.venv/bin/python -m pip install --no-cache-dir /opt/personal-expense \
 && /opt/hermes/.venv/bin/python -c "import expense.handle"
