.PHONY: trace-ls trace-http smoke prepublish clean

trace-ls:
	autoseccomp-gen trace-run "/bin/ls /" -o ls.json

trace-http:
	autoseccomp-gen trace-run "wget -T 5 --tries=1 -qO- http://example.com" -o http.json

smoke: trace-ls trace-http
	./scripts/local_net_smoke.sh

prepublish:
	./scripts/prepublish.sh

clean:
	rm -f ls.json http.json fork.json io.json
