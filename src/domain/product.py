"""
Product domain model with physical constraints.

Restrições (todas aplicadas na criação do objeto):
- Cada dimensão (comprimento, largura, altura) deve estar no intervalo (0, 100] cm.
- A soma das três dimensões deve ser <= 200 cm.
- Peso máximo de 10 kg utilizando gramas como unidade: 0 < peso_em_gramas <= 10000.

Observação: Este modelo assume que os parâmetros de dimensão são dados em centímetros
e o peso é fornecido em gramas (conforme solicitado). Os atributos permanecem nas
mesmas unidades recebidas.
"""


class Product:

    def __init__(self, name: str, weight: float, length: float, width: float, height: float):
        """
        Cria um produto com validação das restrições físicas.

        Args:
            name: Nome do produto.
            weight: Peso em gramas. Deve ser > 0 e <= 10000 (10 kg).
            length: Comprimento em centímetros. Deve ser > 0 e <= 100.
            width: Largura em centímetros. Deve ser > 0 e <= 100.
            height: Altura em centímetros. Deve ser > 0 e <= 100.

        Raises:
            ValueError: Se alguma restrição for violada.
        """
        self._validate_dimensions(length, width, height)
        self._validate_weight(weight)

        self.name = name
        self.weight = float(weight)  # gramas
        self.length = float(length)  # cm
        self.width = float(width)    # cm
        self.height = float(height)  # cm
        self.volume = self.length * self.width * self.height
        self.density = (self.weight / self.volume) if self.volume > 0 else 0

    @staticmethod
    def _validate_dimensions(length: float, width: float, height: float) -> None:
        MAX_SIDE = 100.0  # cm
        MAX_SUM = 200.0   # cm
        for name, value in ("length", length), ("width", width), ("height", height):
            if value is None:
                raise ValueError(f"{name} não pode ser None")
            try:
                v = float(value)
            except Exception:
                raise ValueError(f"{name} deve ser numérico (cm)")
            if v <= 0:
                raise ValueError(f"{name} deve ser > 0 cm")
            if v > MAX_SIDE:
                raise ValueError(f"{name} deve ser <= {MAX_SIDE:.0f} cm")

        if (float(length) + float(width) + float(height)) > MAX_SUM:
            raise ValueError(
                f"A soma das dimensões (C+L+A) deve ser <= {MAX_SUM:.0f} cm"
            )

    @staticmethod
    def _validate_weight(weight: float) -> None:
        MAX_GRAMS = 10_000.0
        if weight is None:
            raise ValueError("peso não pode ser None")
        try:
            w = float(weight)
        except Exception:
            raise ValueError("peso deve ser numérico (gramas)")
        if w <= 0:
            raise ValueError("peso deve ser > 0 g")
        if w > MAX_GRAMS:
            raise ValueError("peso deve ser <= 10000 g (10 kg)")

    def __repr__(self):
        return (f"Product(name={self.name}, weight={self.weight}, length={self.length}, "
                f"width={self.width}, height={self.height}, volume={self.volume}, density={self.density})")

    def __eq__(self, other):
        if not isinstance(other, Product):
            return NotImplemented
        return (
            self.weight == other.weight and
            self.length == other.length and
            self.width == other.width and
            self.height == other.height
        )
    def __hash__(self):
        return hash((self.weight, self.length, self.width, self.height))

        