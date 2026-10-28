import sys, time, markitdown, importlib.metadata as m
t=time.perf_counter()
r = markitdown.MarkItDown().convert(sys.argv[1])
print("markitdown", m.version("markitdown"), "pdfminer", m.version("pdfminer.six"))
print(repr(r.text_content.strip()), f"{(time.perf_counter()-t)*1000:.0f} ms")
