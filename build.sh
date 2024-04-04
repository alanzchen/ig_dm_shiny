pyinstaller wx_app.py --noconfirm  --windowed --hidden-import=pytorch --collect-data torch --collect-data sentence_transformers --copy-metadata torch --copy-metadata tqdm --copy-metadata regex --copy-metadata requests --recursive-copy-metadata packaging --copy-metadata filelock --copy-metadata numpy --copy-metadata tokenizers --copy-metadata importlib_metadata --hidden-import="sklearn.utils._cython_blas" --hidden-import="sklearn.neighbors.typedefs" --hidden-import="sklearn.neighbors.quad_tree" --hidden-import="sklearn.tree" --hidden-import="sklearn.tree._utils" --recursive-copy-metadata tqdm --hidden-import="safetensors" --copy-metadata safetensors --recursive-copy-metadata transformers --copy-metadata pyyaml --hidden-import="pyarrow.vendored.version" 