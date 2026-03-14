import os
import sys
print("----------------sharedddddd")
_current_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(_current_dir)
_shared_path = os.path.join(_root_dir, 'shared')

print("----------------sharedddddd", _shared_path)

if _shared_path not in sys.path:
  sys.path.insert(0, _shared_path)

# del os, sys, _current_dir, _root_dir, _shared_path