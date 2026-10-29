FROM nousresearch/hermes-agent:latest
COPY . /opt/personal-expense
ENV PYTHONPATH=/opt/personal-expense
RUN /opt/hermes/.venv/bin/python -c "import expense.handle"
