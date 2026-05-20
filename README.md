# Local Ollama Wrapper

This repository acts as a chat interface between Llama and the user. The main purpose is to highlight the code with my nvim colors. 

Why midnight? 
Because thats the color of my nvim jeje

# NVIM Setup 

In my nvim setup, using the plugin toggle term I have 
``` lua 
		local llama_term = require("toggleterm.terminal").Terminal:new({
			cmd = "cd /path/to/OllamaCodeCompanion && python main.py",
			direction = "float",
			dir = vim.loop.cwd(),
			id = 3,
		})
```
And I call it with 

``` lua
map("<M-l>", function()
    llama_term:toggle()
    end,"toggle llama")
```

Honestly pretty simple jeje, but useful for having a code companion running locally, safe to prompt and with the colors I like. 

