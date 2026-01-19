import base64
import binascii
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5


class EncryptionHelper:
    @staticmethod
    def encrypt_password(password, modulus_str, exponent_str):
        """
        复刻正方教务系统的 RSA 加密逻辑
        :param password: 明文密码
        :param modulus_str: 模数 (通常是 Hex 字符串)
        :param exponent_str: 指数 (通常是 Hex 字符串，如 '10001')
        :return: 加密后的 Base64 字符串
        """
        try:
            if not modulus_str or not exponent_str:
                print("[JWXT Crypto] Key parameters missing")
                return None

            # 1. 解析公钥参数
            # 正方教务系统 (jsbn.js) 默认使用 Hex 字符串
            modulus = None
            exponent = None

            try:
                # 优先尝试 Hex 解析
                modulus = int(modulus_str, 16)
                exponent = int(exponent_str, 16)
            except ValueError:
                # 如果 Hex 解析失败，且包含非 Hex 字符，尝试 Base64 (旧版兼容)
                print("[JWXT Crypto] Hex parse failed, trying Base64 fallback...")
                try:
                    m_bytes = base64.b64decode(modulus_str)
                    e_bytes = base64.b64decode(exponent_str)
                    modulus = int(binascii.hexlify(m_bytes), 16)
                    exponent = int(binascii.hexlify(e_bytes), 16)
                except Exception as e:
                    print(f"[JWXT Crypto] Base64 fallback failed: {e}")
                    return None

            # 2. 构建公钥对象
            pub_key = RSA.construct((modulus, exponent))

            # 3. 加密 (PKCS1_v1_5)
            cipher = PKCS1_v1_5.new(pub_key)
            encrypted_bytes = cipher.encrypt(password.encode('utf-8'))

            # 4. 结果转 Base64
            return base64.b64encode(encrypted_bytes).decode('utf-8')

        except Exception as e:
            print(f"[JWXT Crypto Error] {str(e)}")
            import traceback
            traceback.print_exc()
            return None