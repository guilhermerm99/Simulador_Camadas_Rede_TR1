# CamadaFisica/test_modulacoes_digitais.py

import unittest
import numpy as np
from modulacoes_digitais import DigitalEncoder

class TestDigitalEncoder(unittest.TestCase):
    def setUp(self):
        self.encoder = DigitalEncoder()

    def test_nrz_polar(self):
        entrada = [1, 0, 1, 0]
        esperado = np.array([1, -1, 1, -1])
        resultado = self.encoder.nrz_polar(entrada)
        np.testing.assert_array_equal(resultado, esperado)

    def test_manchester(self):
        entrada = [1, 0]
        esperado = np.array([1, -1, -1, 1])  # 1 → [1, -1], 0 → [-1, 1]
        resultado = self.encoder.manchester(entrada)
        np.testing.assert_array_equal(resultado, esperado)

    def test_bipolar_ami(self):
        entrada = [1, 0, 1, 1]
        esperado = np.array([1, 0, -1, 1])  # alterna entre +1/-1 para bits 1
        resultado = self.encoder.bipolar_ami(entrada)
        np.testing.assert_array_equal(resultado, esperado)

    def test_encode_dispatch(self):
        entrada = [0, 1]
        self.assertTrue(np.array_equal(self.encoder.encode(entrada, "NRZ-Polar"), self.encoder.nrz_polar(entrada)))
        self.assertTrue(np.array_equal(self.encoder.encode(entrada, "Manchester"), self.encoder.manchester(entrada)))
        self.assertTrue(np.array_equal(self.encoder.encode(entrada, "Bipolar"), self.encoder.bipolar_ami(entrada)))
        with self.assertRaises(ValueError):
            self.encoder.encode(entrada, "Inexistente")

if __name__ == '__main__':
    unittest.main()
