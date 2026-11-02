import unittest

from fabrica.catalog import ProcedureCatalog
from fabrica.domain import ProcedureDefinition


class ProcedureCatalogTests(unittest.TestCase):
    def test_selects_the_explicit_active_version(self):
        catalog = ProcedureCatalog()
        catalog.register(
            ProcedureDefinition(
                procedure_id="prepare-report",
                version="1.0",
                name="Preparar informe",
                description="Reúne la información necesaria para un informe.",
                severity="low",
            )
        )
        catalog.register(
            ProcedureDefinition(
                procedure_id="prepare-report",
                version="2.0",
                name="Preparar informe",
                description="Reúne la información y valida sus fuentes.",
                severity="medium",
            )
        )

        catalog.activate("prepare-report", "2.0")

        selected = catalog.get_active("prepare-report")
        self.assertEqual(selected.version, "2.0")
        self.assertEqual(selected.severity, "medium")

    def test_does_not_activate_an_unknown_version(self):
        catalog = ProcedureCatalog()
        catalog.register(
            ProcedureDefinition(
                procedure_id="classify-request",
                version="1.0",
                name="Clasificar petición",
                description="Propone un procedimiento para una petición.",
                severity="low",
            )
        )

        with self.assertRaises(KeyError):
            catalog.activate("classify-request", "9.9")


if __name__ == "__main__":
    unittest.main()
