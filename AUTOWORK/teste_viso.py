import cv2
import mediapipe as mp
import math
import time
import os
import urllib.request
import numpy as np


# ============================================================
# CONFIGURAÇÕES
# ============================================================

CAMERA_INDEX = 0

TEMPO_ATIVACAO = 5.0

# Distância máxima entre polegar e indicador
PINCH_THRESHOLD = 0.07

MODEL_PATH = "hand_landmarker.task"

MODEL_URL = (
    "https://storage.googleapis.com/"
    "mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/"
    "hand_landmarker.task"
)


# ============================================================
# MODELO DO MEDIAPIPE
# ============================================================

def garantir_modelo():

    if os.path.exists(MODEL_PATH):
        return

    print("Modelo do MediaPipe não encontrado.")
    print("Baixando modelo...")

    try:

        urllib.request.urlretrieve(
            MODEL_URL,
            MODEL_PATH
        )

        print("Modelo baixado com sucesso.")

    except Exception as erro:

        print("Erro ao baixar o modelo:")
        print(erro)

        raise


# ============================================================
# DISTÂNCIA ENTRE PONTOS
# ============================================================

def distancia(a, b):

    return math.sqrt(
        (a.x - b.x) ** 2 +
        (a.y - b.y) ** 2 +
        (a.z - b.z) ** 2
    )


# ============================================================
# DETECTAR PINÇA
# ============================================================

def detectar_pinca(landmarks):

    polegar = landmarks[4]
    indicador = landmarks[8]

    return distancia(
        polegar,
        indicador
    ) < PINCH_THRESHOLD


# ============================================================
# CONTAR DEDOS
# ============================================================

def contar_dedos(landmarks):

    dedos = 0

    # Indicador
    if landmarks[8].y < landmarks[6].y:
        dedos += 1

    # Médio
    if landmarks[12].y < landmarks[10].y:
        dedos += 1

    # Anelar
    if landmarks[16].y < landmarks[14].y:
        dedos += 1

    # Mindinho
    if landmarks[20].y < landmarks[18].y:
        dedos += 1

    # Polegar
    if distancia(
        landmarks[4],
        landmarks[17]
    ) > distancia(
        landmarks[3],
        landmarks[17]
    ):
        dedos += 1

    return dedos


# ============================================================
# DESENHAR MÃO
# ============================================================

def desenhar_mao(frame, landmarks):

    altura, largura = frame.shape[:2]

    pontos = []

    for ponto in landmarks:

        x = int(ponto.x * largura)
        y = int(ponto.y * altura)

        pontos.append((x, y))

    # Conexões da mão
    conexoes = [

        # Polegar
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 4),

        # Indicador
        (0, 5),
        (5, 6),
        (6, 7),
        (7, 8),

        # Médio
        (5, 9),
        (9, 10),
        (10, 11),
        (11, 12),

        # Anelar
        (9, 13),
        (13, 14),
        (14, 15),
        (15, 16),

        # Mindinho
        (13, 17),
        (17, 18),
        (18, 19),
        (19, 20),

        # Palma
        (0, 17)
    ]

    for a, b in conexoes:

        cv2.line(
            frame,
            pontos[a],
            pontos[b],
            (255, 255, 255),
            2
        )

    # Pontos da mão
    for i, ponto in enumerate(pontos):

        cv2.circle(
            frame,
            ponto,
            5,
            (255, 255, 255),
            -1
        )

    # Indicador em destaque
    cv2.circle(
        frame,
        pontos[8],
        10,
        (0, 255, 0),
        -1
    )

    return pontos


# ============================================================
# RECONHECER FORMA
# ============================================================

def reconhecer_forma(trajetoria):

    if len(trajetoria) < 15:
        return None, None

    pontos = np.array(
        trajetoria,
        dtype=np.float32
    )

    # --------------------------------------------------------
    # Suavizar trajetória
    # --------------------------------------------------------

    if len(pontos) >= 5:

        suavizados = []

        for i in range(len(pontos)):

            inicio = max(0, i - 2)
            fim = min(
                len(pontos),
                i + 3
            )

            media = np.mean(
                pontos[inicio:fim],
                axis=0
            )

            suavizados.append(media)

        pontos = np.array(
            suavizados,
            dtype=np.float32
        )

    pontos_int = pontos.astype(
        np.int32
    )

    # --------------------------------------------------------
    # Bounding box
    # --------------------------------------------------------

    x, y, largura, altura = cv2.boundingRect(
        pontos_int
    )

    if largura < 20 or altura < 20:
        return None, None

    proporcao = largura / float(altura)

    # --------------------------------------------------------
    # Verificar se parece uma linha
    # --------------------------------------------------------

    distancia_extremos = np.linalg.norm(
        pontos[0] - pontos[-1]
    )

    comprimento = cv2.arcLength(
        pontos.reshape(-1, 1, 2),
        False
    )

    if comprimento > 0:

        linearidade = (
            distancia_extremos /
            comprimento
        )

        if linearidade > 0.80:

            return "LINHA", pontos_int

    # --------------------------------------------------------
    # Contorno
    # --------------------------------------------------------

    contorno = pontos_int.reshape(
        -1,
        1,
        2
    )

    perimetro = cv2.arcLength(
        contorno,
        True
    )

    if perimetro == 0:
        return None, None

    epsilon = 0.04 * perimetro

    aproximado = cv2.approxPolyDP(
        contorno,
        epsilon,
        True
    )

    vertices = len(aproximado)

    # --------------------------------------------------------
    # TRIÂNGULO
    # --------------------------------------------------------

    if vertices == 3:

        return (
            "TRIÂNGULO",
            aproximado
        )

    # --------------------------------------------------------
    # QUADRADO / RETÂNGULO
    # --------------------------------------------------------

    if vertices == 4:

        if 0.85 <= proporcao <= 1.15:

            return (
                "QUADRADO",
                aproximado
            )

        return (
            "RETÂNGULO",
            aproximado
        )

    # --------------------------------------------------------
    # CÍRCULO
    # --------------------------------------------------------

    area = cv2.contourArea(
        contorno
    )

    if area > 0:

        circularidade = (
            4 *
            math.pi *
            area
        ) / (
            perimetro ** 2
        )

        if circularidade > 0.70:

            return (
                "CÍRCULO",
                contorno
            )

    # --------------------------------------------------------
    # FORMA DESCONHECIDA
    # --------------------------------------------------------

    return (
        "FORMA",
        aproximado
    )


# ============================================================
# DESENHAR FORMA
# ============================================================

def desenhar_forma(
    frame,
    tipo,
    pontos
):

    if pontos is None:
        return frame

    overlay = frame.copy()

    pontos = pontos.reshape(
        -1,
        2
    ).astype(np.int32)

    # --------------------------------------------------------
    # LINHA
    # --------------------------------------------------------

    if tipo == "LINHA":

        if len(pontos) >= 2:

            cv2.line(
                frame,
                tuple(pontos[0]),
                tuple(pontos[-1]),
                (255, 100, 0),
                4
            )

        return frame

    # --------------------------------------------------------
    # CÍRCULO
    # --------------------------------------------------------

    if tipo == "CÍRCULO":

        (cx, cy), raio = cv2.minEnclosingCircle(
            pontos
        )

        centro = (
            int(cx),
            int(cy)
        )

        raio = int(raio)

        cv2.circle(
            overlay,
            centro,
            raio,
            (255, 100, 0),
            -1
        )

        cv2.circle(
            frame,
            centro,
            raio,
            (255, 100, 0),
            3
        )

    # --------------------------------------------------------
    # OUTRAS FORMAS
    # --------------------------------------------------------

    else:

        cv2.fillPoly(
            overlay,
            [pontos],
            (255, 100, 0)
        )

        cv2.polylines(
            frame,
            [pontos],
            True,
            (255, 100, 0),
            3
        )

    # Transparência
    frame[:] = cv2.addWeighted(
        overlay,
        0.35,
        frame,
        0.65,
        0
    )

    return frame


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main():

    garantir_modelo()

    # ========================================================
    # API NOVA DO MEDIAPIPE
    # ========================================================

    BaseOptions = mp.tasks.BaseOptions

    VisionRunningMode = (
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
            model_asset_path=MODEL_PATH
        ),

        running_mode=VisionRunningMode.VIDEO,

        num_hands=2,

        min_hand_detection_confidence=0.6,

        min_hand_presence_confidence=0.6,

        min_tracking_confidence=0.6
    )

    # ========================================================
    # CÂMERA
    # ========================================================

    camera = cv2.VideoCapture(
        CAMERA_INDEX
    )

    if not camera.isOpened():

        print("ERRO: não foi possível abrir a câmera.")

        return

    camera.set(
        cv2.CAP_PROP_FRAME_WIDTH,
        1280
    )

    camera.set(
        cv2.CAP_PROP_FRAME_HEIGHT,
        720
    )

    # ========================================================
    # ESTADOS
    # ========================================================

    ativado = False

    inicio_ativacao = None

    trajetoria = []

    desenhando = False

    formas = []

    timestamp = 0

    print()
    print("=" * 60)
    print("AUTOWORK - VISÃO COMPUTACIONAL")
    print("=" * 60)
    print()
    print("1. Coloque sua mão na frente da câmera.")
    print("2. Aguarde 5 segundos.")
    print("3. Use o indicador para desenhar.")
    print("4. Faça uma pinça para confirmar.")
    print()
    print("R = limpar formas")
    print("Q / ESC = sair")
    print()

    # ========================================================
    # MEDIAPIPE
    # ========================================================

    with HandLandmarker.create_from_options(
        options
    ) as detector:

        while True:

            sucesso, frame = camera.read()

            if not sucesso:
                break

            # Espelhar câmera
            frame = cv2.flip(
                frame,
                1
            )

            altura, largura = frame.shape[:2]

            # =================================================
            # CONVERTER PARA RGB
            # =================================================

            rgb = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )

            imagem_mp = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=rgb
            )

            timestamp += 33

            resultado = detector.detect_for_video(
                imagem_mp,
                timestamp
            )

            maos = resultado.hand_landmarks

            mao_detectada = len(maos) > 0

            # =================================================
            # ATIVAÇÃO
            # =================================================

            if not ativado:

                if mao_detectada:

                    if inicio_ativacao is None:

                        inicio_ativacao = time.time()

                    tempo = (
                        time.time()
                        - inicio_ativacao
                    )

                    progresso = min(
                        tempo /
                        TEMPO_ATIVACAO,
                        1.0
                    )

                    percentual = int(
                        progresso * 100
                    )

                    cv2.putText(
                        frame,
                        "ATIVANDO AUTOWORK",
                        (40, 60),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1.0,
                        (255, 255, 255),
                        2
                    )

                    cv2.putText(
                        frame,
                        f"{percentual}%",
                        (40, 110),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.9,
                        (255, 255, 255),
                        2
                    )

                    # Barra
                    cv2.rectangle(
                        frame,
                        (40, 135),
                        (340, 160),
                        (80, 80, 80),
                        -1
                    )

                    cv2.rectangle(
                        frame,
                        (40, 135),
                        (
                            40 +
                            int(300 * progresso),
                            160
                        ),
                        (255, 100, 0),
                        -1
                    )

                    if tempo >= TEMPO_ATIVACAO:

                        ativado = True

                        inicio_ativacao = None

                        print(
                            "AUTOWORK VISÃO: ATIVADO"
                        )

                else:

                    inicio_ativacao = None

                    cv2.putText(
                        frame,
                        "MOSTRE SUA MAO",
                        (40, 60),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1.0,
                        (255, 255, 255),
                        2
                    )

            # =================================================
            # SISTEMA ATIVADO
            # =================================================

            else:

                cv2.putText(
                    frame,
                    "AUTOWORK: ATIVO",
                    (40, 45),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (255, 255, 255),
                    2
                )

                # ------------------------------------------------
                # PROCESSAR MÃOS
                # ------------------------------------------------

                for indice_mao, landmarks in enumerate(maos):

                    pontos = desenhar_mao(
                        frame,
                        landmarks
                    )

                    dedos = contar_dedos(
                        landmarks
                    )

                    pinca = detectar_pinca(
                        landmarks
                    )

                    # ------------------------------------------------
                    # INFORMAÇÕES
                    # ------------------------------------------------

                    cv2.putText(
                        frame,
                        f"MAO {indice_mao + 1}",
                        (40, 90 + indice_mao * 100),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (255, 255, 255),
                        2
                    )

                    cv2.putText(
                        frame,
                        f"DEDOS: {dedos}",
                        (40, 120 + indice_mao * 100),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (255, 255, 255),
                        2
                    )

                    # ------------------------------------------------
                    # PINÇA
                    # ------------------------------------------------

                    if pinca:

                        cv2.line(
                            frame,
                            pontos[4],
                            pontos[8],
                            (0, 255, 255),
                            3
                        )

                        cv2.putText(
                            frame,
                            "PINCA - CONFIRMAR",
                            (40, 150 + indice_mao * 100),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.65,
                            (0, 255, 255),
                            2
                        )

                    # ------------------------------------------------
                    # DESENHO
                    # ------------------------------------------------

                    indicador = pontos[8]

                    if not pinca:

                        if not desenhando:

                            trajetoria = []

                            desenhando = True

                        trajetoria.append(
                            indicador
                        )

                    else:

                        if desenhando:

                            desenhando = False

                            tipo, pontos_forma = reconhecer_forma(
                                trajetoria
                            )

                            if tipo is not None:

                                formas.append(
                                    (
                                        tipo,
                                        pontos_forma.copy()
                                    )
                                )

                                print(
                                    f"Forma reconhecida: {tipo}"
                                )

                            trajetoria = []

                # =================================================
                # DESENHAR TRAJETÓRIA
                # =================================================

                if len(trajetoria) > 1:

                    pontos_trajetoria = np.array(
                        trajetoria,
                        dtype=np.int32
                    )

                    cv2.polylines(
                        frame,
                        [pontos_trajetoria],
                        False,
                        (255, 100, 0),
                        3
                    )

                # =================================================
                # DESENHAR FORMAS CONFIRMADAS
                # =================================================

                for tipo, pontos_forma in formas:

                    desenhar_forma(
                        frame,
                        tipo,
                        pontos_forma
                    )

                # =================================================
                # MOSTRAR ÚLTIMA FORMA
                # =================================================

                if formas:

                    ultima_forma = formas[-1][0]

                    cv2.putText(
                        frame,
                        f"FORMA: {ultima_forma}",
                        (40, altura - 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (255, 255, 255),
                        2
                    )

            # =================================================
            # MOSTRAR CÂMERA
            # =================================================

            cv2.imshow(
                "AUTOWORK - Visao",
                frame
            )

            tecla = cv2.waitKey(1) & 0xFF

            # Limpar
            if tecla == ord("r"):

                trajetoria = []

                formas = []

                desenhando = False

                print(
                    "Formas apagadas."
                )

            # Sair
            if tecla == ord("q") or tecla == 27:

                break

    # ========================================================
    # FINALIZAR
    # ========================================================

    camera.release()

    cv2.destroyAllWindows()

    print()
    print("AUTOWORK Visão encerrado.")


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":
    main()