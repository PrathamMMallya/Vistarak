FROM ollama/ollama:latest

ENV OLLAMA_HOST=0.0.0.0:11434

COPY ollama/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 11434

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
