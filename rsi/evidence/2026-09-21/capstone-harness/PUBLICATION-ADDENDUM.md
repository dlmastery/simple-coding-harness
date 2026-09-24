# Complete the exported provenance handoff

The exported package's provenance points to an enclosing SOURCES.csv. The first export copied the package but omitted that surrounding metadata. Execution and its identities were already verified; the missing handoff files did not affect training.

After sealing the 138-file run manifest, publication added export/SOURCES.csv and export/PACKAGE-HASHES.csv as byte-identical copies of the original top-level files. The same supplement was added to the sibling workspace. PUBLICATION-SUPPLEMENTS.csv records their hashes. The original manifest and executed package remain unchanged.

The maintained author driver now carries these two files during future exports. Historical driver versions remain unchanged so the original omission can be inspected. Transfer the exported package together with its surrounding provenance files.
