
import cv2
import mediapipe as mp
import numpy as np
import math
import time


# ============================================================
# CONFIGURAÇÕES
# ============================================================

CAMERA_INDEX = 0

LARGURA = 1280
ALTURA = 720

RAIO_INICIAL = 150
RAIO_MINIMO = 80
RAIO_MAXIMO = 320

PINCH_THRESHOLD = 0.075
SUAVIZACAO = 0.18


# ============================================================
# ESFERA AUTOWORK
# ============================================================

class EsferaAutowork:

    def __init__(self, largura, altura):

        self.largura = largura
        self.altura = altura

        self.x = largura // 2
        self.y = altura // 2

        self.x_alvo = self.x
        self.y_alvo = self.y

        self.raio = RAIO_INICIAL
        self.raio_alvo = RAIO_INICIAL

        self.arrastando = False

        self.inicio = time.time()

        self.particulas = []

        for _ in range(70):

            self.particulas.append({
                "angulo": np.random.uniform(
                    0,
                    math.pi * 2
                ),
                "distancia": np.random.uniform(
                    RAIO_INICIAL * 0.9,
                    RAIO_INICIAL * 1.7
                ),
                "velocidade": np.random.uniform(
                    0.15,
                    0.5
                ),
                "tamanho": np.random.uniform(
                    1,
                    3
                )
            })

    # ========================================================
    # MOVER
    # ========================================================

    def mover(self, x, y):

        self.x_alvo = int(
            np.clip(
                x,
                self.raio,
                self.largura - self.raio
            )
        )

        self.y_alvo = int(
            np.clip(
                y,
                self.raio,
                self.altura - self.raio
            )
        )

    # ========================================================
    # TAMANHO
    # ========================================================

    def definir_tamanho(self, raio):

        self.raio_alvo = int(
            np.clip(
                raio,
                RAIO_MINIMO,
                RAIO_MAXIMO
            )
        )

    # ========================================================
    # ATUALIZAR
    # ========================================================

    def atualizar(self):

        self.x += (
            self.x_alvo - self.x
        ) * SUAVIZACAO

        self.y += (
            self.y_alvo - self.y
        ) * SUAVIZACAO

        self.raio += (
            self.raio_alvo - self.raio
        ) * 0.15

    # ========================================================
    # GLOW
    # ========================================================

    def desenhar_glow(self, frame):

        centro = (
            int(self.x),
            int(self.y)
        )

        raio = int(self.raio)

        for nivel in range(7, 0, -1):

            camada = frame.copy()

            tamanho = int(
                raio * (
                    1.0 +
                    nivel * 0.08
                )
            )

            cv2.circle(
                camada,
                centro,
                tamanho,
                (255, 90, 20),
                -1
            )

            intensidade = (
                0.012 * nivel
            )

            frame = cv2.addWeighted(
                camada,
                intensidade,
                frame,
                1 - intensidade,
                0
            )

        return frame

    # ========================================================
    # ESFERA
    # ========================================================

    def desenhar_esfera(self, frame):

        altura, largura = frame.shape[:2]

        cx = int(self.x)
        cy = int(self.y)
        raio = int(self.raio)

        overlay = frame.copy()

        y_inicio = max(
            0,
            cy - raio
        )

        y_fim = min(
            altura,
            cy + raio
        )

        x_inicio = max(
            0,
            cx - raio
        )

        x_fim = min(
            largura,
            cx + raio
        )

        for y in range(
            y_inicio,
            y_fim
        ):

            dy = y - cy

            for x in range(
                x_inicio,
                x_fim
            ):

                dx = x - cx

                distancia = math.sqrt(
                    dx * dx +
                    dy * dy
                )

                if distancia > raio:
                    continue

                intensidade = (
                    1 -
                    distancia / raio
                )

                luz = max(
                    0,
                    1 -
                    math.sqrt(
                        (
                            dx +
                            raio * 0.35
                        ) ** 2 +
                        (
                            dy +
                            raio * 0.35
                        ) ** 2
                    ) / (
                        raio * 1.4
                    )
                )

                azul = int(
                    80 +
                    170 *
                    intensidade
                )

                verde = int(
                    40 +
                    100 *
                    intensidade
                )

                vermelho = int(
                    5 +
                    35 *
                    intensidade
                )

                fator = (
                    0.7 +
                    luz * 0.5
                )

                azul = min(
                    255,
                    int(azul * fator)
                )

                verde = min(
                    255,
                    int(verde * fator)
                )

                vermelho = min(
                    255,
                    int(vermelho * fator)
                )

                overlay[y, x] = (
                    azul,
                    verde,
                    vermelho
                )

        frame = cv2.addWeighted(
            overlay,
            0.60,
            frame,
            0.40,
            0
        )

        return frame

    # ========================================================
    # ANÉIS
    # ========================================================

    def desenhar_aneis(self, frame):

        tempo = (
            time.time() -
            self.inicio
        )

        centro = (
            int(self.x),
            int(self.y)
        )

        raio = int(self.raio)

        # Anel horizontal

        cv2.ellipse(
            frame,
            centro,
            (
                int(raio * 1.30),
                int(raio * 0.38)
            ),
            math.sin(tempo * 0.5) * 20,
            0,
            360,
            (255, 150, 50),
            2,
            cv2.LINE_AA
        )

        # Anel vertical

        cv2.ellipse(
            frame,
            centro,
            (
                int(raio * 1.05),
                int(raio * 0.30)
            ),
            90 +
            math.sin(tempo * 0.7) * 25,
            0,
            360,
            (180, 110, 40),
            1,
            cv2.LINE_AA
        )

        # Anel externo

        cv2.ellipse(
            frame,
            centro,
            (
                int(raio * 1.45),
                int(raio * 0.20)
            ),
            -35 +
            math.sin(tempo * 0.4) * 20,
            0,
            360,
            (150, 90, 30),
            1,
            cv2.LINE_AA
        )

    # ========================================================
    # PARTÍCULAS
    # ========================================================

    def desenhar_particulas(self, frame):

        tempo = (
            time.time() -
            self.inicio
        )

        for particula in self.particulas:

            angulo = (
                particula["angulo"] +
                tempo *
                particula["velocidade"]
            )

            distancia = (
                particula["distancia"] +
                math.sin(
                    tempo *
                    particula["velocidade"]
                ) * 8
            )

            x = int(
                self.x +
                math.cos(angulo) *
                distancia
            )

            y = int(
                self.y +
                math.sin(angulo) *
                distancia *
                0.65
            )

            if (
                0 <= x < self.largura
                and
                0 <= y < self.altura
            ):

                cv2.circle(
                    frame,
                    (x, y),
                    int(particula["tamanho"]),
                    (200, 130, 50),
                    -1,
                    cv2.LINE_AA
                )

    # ========================================================
    # NÚCLEO
    # ========================================================

    def desenhar_nucleo(self, frame):

        tempo = (
            time.time() -
            self.inicio
        )

        pulsacao = (
            math.sin(
                tempo * 3
            ) + 1
        ) / 2

        raio = int(
            self.raio *
            (
                0.10 +
                pulsacao * 0.025
            )
        )

        cv2.circle(
            frame,
            (
                int(self.x),
                int(self.y)
            ),
            raio,
            (255, 220, 150),
            -1,
            cv2.LINE_AA
        )

        cv2.circle(
            frame,
            (
                int(self.x),
                int(self.y)
            ),
            raio + 5,
            (180, 130, 60),
            1,
            cv2.LINE_AA
        )

    # ========================================================
    # TEXTO
    # ========================================================

    def desenhar_texto(self, frame):

        texto = "AUTOWORK"

        fonte = cv2.FONT_HERSHEY_DUPLEX

        escala = max(
            0.55,
            self.raio / 190
        )

        tamanho = cv2.getTextSize(
            texto,
            fonte,
            escala,
            1
        )[0]

        x = int(
            self.x -
            tamanho[0] / 2
        )

        y = int(
            self.y +
            tamanho[1] / 2
        )

        # Sombra

        cv2.putText(
            frame,
            texto,
            (
                x + 2,
                y + 2
            ),
            fonte,
            escala,
            (10, 10, 10),
            3,
            cv2.LINE_AA
        )

        # Texto

        cv2.putText(
            frame,
            texto,
            (x, y),
            fonte,
            escala,
            (220, 200, 160),
            1,
            cv2.LINE_AA
        )

    # ========================================================
    # DESENHAR
    # ========================================================

    def desenhar(self, frame):

        self.atualizar()

        frame = self.desenhar_glow(
            frame
        )

        frame = self.desenhar_esfera(
            frame
        )

        self.desenhar_particulas(
            frame
        )

        self.desenhar_aneis(
            frame
        )

        self.desenhar_nucleo(
            frame
        )

        self.desenhar_texto(
            frame
        )

        if self.arrastando:

            cv2.circle(
                frame,
                (
                    int(self.x),
                    int(self.y)
                ),
                int(self.raio * 1.15),
                (255, 180, 80),
                2,
                cv2.LINE_AA
            )

        return frame


# ============================================================
# DISTÂNCIA DA MÃO
# ============================================================

def distancia(a, b):

    return math.sqrt(
        (a.x - b.x) ** 2 +
        (a.y - b.y) ** 2
    )


# ============================================================
# DETECTAR PINÇA
# ============================================================

def detectar_pinca(landmarks):

    polegar = landmarks[4]
    indicador = landmarks[8]

    return (
        distancia(
            polegar,
            indicador
        )
        <
        PINCH_THRESHOLD
    )


# ============================================================
# CRIAR MEDIAPIPE
# ============================================================

def criar_detector():

    BaseOptions = (
        mp.tasks.BaseOptions
    )

    RunningMode = (
        mp.tasks.vision.RunningMode
    )

    HandLandmarker = (
        mp.tasks.vision.HandLandmarker
    )

    HandLandmarkerOptions = (
        mp.tasks.vision.HandLandmarkerOptions
    )

    options = HandLandmarkerOptions(

        base_options=BaseOptions(
            model_asset_path=
            "hand_landmarker.task"
        ),

        running_mode=RunningMode.VIDEO,

        num_hands=1,

        min_hand_detection_confidence=0.6,

        min_hand_presence_confidence=0.6,

        min_tracking_confidence=0.6
    )

    return HandLandmarker.create_from_options(
        options
    )


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main():

    camera = cv2.VideoCapture(
        CAMERA_INDEX
    )

    if not camera.isOpened():

        print(
            "ERRO: câmera não encontrada."
        )

        return

    camera.set(
        cv2.CAP_PROP_FRAME_WIDTH,
        LARGURA
    )

    camera.set(
        cv2.CAP_PROP_FRAME_HEIGHT,
        ALTURA
    )

    janela = (
        "AUTOWORK - VISION"
    )

    cv2.namedWindow(
        janela,
        cv2.WINDOW_NORMAL
    )

    # Tela cheia

    cv2.setWindowProperty(
        janela,
        cv2.WND_PROP_FULLSCREEN,
        cv2.WINDOW_FULLSCREEN
    )

    esfera = EsferaAutowork(
        LARGURA,
        ALTURA
    )

    timestamp = 0

    pinça_anterior = False

    distancia_inicial = None
    raio_inicial = None

    print()
    print("=" * 60)
    print("AUTOWORK VISION")
    print("=" * 60)
    print()
    print("🤏 Pinça + movimento = mover")
    print("🤏 Aproximar/afastar = tamanho")
    print("R = restaurar")
    print("ESC = sair")
    print()

    with criar_detector() as detector:

        while True:

            sucesso, frame = (
                camera.read()
            )

            if not sucesso:
                break

            frame = cv2.flip(
                frame,
                1
            )

            altura, largura = (
                frame.shape[:2]
            )

            # ------------------------------------------------
            # MediaPipe
            # ------------------------------------------------

            rgb = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )

            imagem = mp.Image(
                image_format=
                mp.ImageFormat.SRGB,
                data=rgb
            )

            timestamp += 33

            resultado = (
                detector.detect_for_video(
                    imagem,
                    timestamp
                )
            )

            maos = (
                resultado.hand_landmarks
            )

            # =================================================
            # MÃO DETECTADA
            # =================================================

            if maos:

                landmarks = maos[0]

                indicador = landmarks[8]

                pinca = detectar_pinca(
                    landmarks
                )

                indicador_x = int(
                    indicador.x *
                    largura
                )

                indicador_y = int(
                    indicador.y *
                    altura
                )

                # ------------------------------------------------
                # Pinça
                # ------------------------------------------------

                if pinca:

                    esfera.arrastando = True

                    # Primeiro frame da pinça

                    if not pinça_anterior:

                        distancia_inicial = (
                            distancia(
                                landmarks[4],
                                landmarks[8]
                            )
                        )

                        raio_inicial = (
                            esfera.raio
                        )

                    # ------------------------------------------------
                    # MOVER ESFERA
                    # ------------------------------------------------

                    esfera.mover(
                        indicador_x,
                        indicador_y
                    )

                    # ------------------------------------------------
                    # ALTERAR TAMANHO
                    # ------------------------------------------------

                    distancia_atual = (
                        distancia(
                            landmarks[4],
                            landmarks[8]
                        )
                    )

                    if distancia_inicial:

                        diferenca = (
                            distancia_atual -
                            distancia_inicial
                        )

                        novo_raio = (
                            raio_inicial +
                            diferenca * 1800
                        )

                        esfera.definir_tamanho(
                            novo_raio
                        )

                    # ------------------------------------------------
                    # Linha entre polegar e indicador
                    # ------------------------------------------------

                    polegar = landmarks[4]

                    polegar_x = int(
                        polegar.x *
                        largura
                    )

                    polegar_y = int(
                        polegar.y *
                        altura
                    )

                    cv2.line(
                        frame,
                        (
                            polegar_x,
                            polegar_y
                        ),
                        (
                            indicador_x,
                            indicador_y
                        ),
                        (255, 200, 100),
                        3,
                        cv2.LINE_AA
                    )

                else:

                    esfera.arrastando = False

                    distancia_inicial = None
                    raio_inicial = None

                pinça_anterior = pinca

            else:

                esfera.arrastando = False

                pinça_anterior = False

                distancia_inicial = None
                raio_inicial = None

            # =================================================
            # ESFERA
            # =================================================

            frame = esfera.desenhar(
                frame
            )

            # =================================================
            # INFORMAÇÃO
            # =================================================

            cv2.putText(
                frame,
                "AUTOWORK VISION",
                (30, 45),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (190, 160, 110),
                1,
                cv2.LINE_AA
            )

            if esfera.arrastando:

                cv2.putText(
                    frame,
                    "CONTROLE ATIVO",
                    (30, 80),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (220, 190, 130),
                    1,
                    cv2.LINE_AA
                )

            # =================================================
            # MOSTRAR
            # =================================================

            cv2.imshow(
                janela,
                frame
            )

            tecla = (
                cv2.waitKey(1) &
                0xFF
            )

            # =================================================
            # RESTAURAR
            # =================================================

            if tecla == ord("r"):

                esfera.x = (
                    largura // 2
                )

                esfera.y = (
                    altura // 2
                )

                esfera.x_alvo = (
                    largura // 2
                )

                esfera.y_alvo = (
                    altura // 2
                )

                esfera.raio = (
                    RAIO_INICIAL
                )

                esfera.raio_alvo = (
                    RAIO_INICIAL
                )

            # =================================================
            # SAIR
            # =================================================

            if tecla == 27:
                break

    camera.release()

    cv2.destroyAllWindows()

    print(
        "AUTOWORK Vision encerrado."
    )


# ============================================================
# EXECUTAR
# ============================================================

if __name__ == "__main__":
    main()

