from __future__ import annotations

import html
import random
import string
from datetime import datetime, timedelta
from typing import Optional

from app.models.loan import Loan
from app.models.product import Product
from app.models.purchase_contract import PurchaseContractSignature
from app.models.user import User


PARTY_A_NAME = "广州芒果数科科技服务有限公司"
PARTY_A_LEGAL_PERSON = "邓伟强"


def generate_contract_no(now: Optional[datetime] = None) -> str:
    current = now or datetime.now()
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"XHBHT{current.strftime('%Y%m%d%H%M%S')}{suffix}"


def _money(value) -> str:
    amount = float(value or 0)
    return f"{amount:.2f}"


def _safe(value, default: str = "") -> str:
    text = str(value if value not in (None, "") else default)
    return html.escape(text)


def build_contract_payload(
    *,
    user: User,
    loan: Loan,
    product: Product,
    order_no: str,
    use_discount: bool = False,
    signed_at: Optional[datetime] = None,
) -> dict:
    now = signed_at or datetime.now()
    ecard_face_value = float(product.ecard_face_value or 0)
    rights_price = float(product.rights_price or 0)
    available_discount = float(getattr(loan, "approval_discount_amount", 0) or 0)
    discount_amount = min(available_discount, rights_price) if use_discount else 0.0
    payment_amount = max(float(product.payment_amount or 0) - discount_amount, 0.0)
    effective_rights_price = max(rights_price - discount_amount, 0.0)
    term_days = int((getattr(loan, "term_days", None) or product.term_days or 7) or 7)
    due_date = now + timedelta(days=term_days)
    due_date_text = f"{due_date.strftime('%Y年%m月%d日')}（发卡成功后按实际账期同步）"
    product_name = product.name
    if ecard_face_value <= 0:
        spec = "纯权益包 1 份"
    else:
        spec = f"京东E卡{_money(ecard_face_value)}元 + {product.rights_title or '旅游权益'} 1 份"
    address = getattr(user, "id_address", None) or "虚拟商品，以卡密形式交付，无需实际物流发货"

    rows = [
        ("甲方", PARTY_A_NAME),
        ("法人", PARTY_A_LEGAL_PERSON),
        ("乙方", user.name or ""),
        ("身份证", user.id_card_num or ""),
        ("手机号", user.phone or ""),
        ("商品名称", product_name),
        ("规格", spec),
        ("数量", "1"),
        ("销售单价", f"{_money(payment_amount)} 元"),
        ("平台订单号", order_no),
        ("账单总金额", f"{_money(payment_amount)} 元"),
        ("账期", f"{term_days} 天"),
        ("账单到期日", due_date_text),
        ("账单金额", f"{_money(payment_amount)} 元"),
        ("收件人", user.name or ""),
        ("联系号码", user.phone or ""),
        ("邮寄地址", "虚拟商品，以卡密形式交付，无需实际物流发货"),
        ("交付方式", "电子形式发送"),
        ("E卡面值", f"{_money(ecard_face_value)} 元"),
        ("权益金额", f"{_money(effective_rights_price)} 元"),
        ("抵扣金额", f"{_money(discount_amount)} 元"),
        ("签署时间", now.strftime("%Y-%m-%d %H:%M:%S")),
    ]
    summary_html = "".join(
        f"<tr><th>{_safe(label)}</th><td>{_safe(value)}</td></tr>"
        for label, value in rows
    )

    html_content = f"""
<article class="purchase-contract">
  <h1>商品购销合同</h1>
  <table class="contract-summary"><tbody>{summary_html}</tbody></table>
  <section>
    <p>各方已签署《商品购销合同》，现本着平等、诚实信用、实惠互利原则，经友好协商一致，共同签署本合同如下。</p>
    <p>本协议是在本平台上为符合相应条件的注册用户购买平台上所展示的商品，就该商品或服务的相关事宜所订立的合同。用户通过勾选或点击同意本合同协议，即表示同意以电子合同形式签订本合同，本协议构成对各方有约束力的法律文件。</p>
  </section>
  <section>
    <h2>一、销售商品信息</h2>
    <p>商品名称：{_safe(product_name)}；规格：{_safe(spec)}；数量：1；销售单价：{_money(payment_amount)} 元；平台订单号：{_safe(order_no)}。</p>
    <p>乙方确认订单信息与商品详情页展示内容完全一致，不得以商品描述存在理解歧义为由主张权利。</p>
  </section>
  <section>
    <h2>二、商品交付</h2>
    <p>收件人：{_safe(user.name)}；联系号码：{_safe(user.phone)}；邮寄地址：虚拟商品，以卡密形式交付，无需实际物流发货；邮寄费用：无；交付方式：电子形式发送。</p>
    <p>乙方应当及时签收商品并核对商品内容。虚拟商品定制发货后合同立即生效，商品概不退换，法律或平台规则另有规定的除外。</p>
  </section>
  <section>
    <h2>三、商品货款及付款方式</h2>
    <p>本协议支付方式为：【先发货后支付】。账单总金额：{_money(payment_amount)} 元；账期：{term_days} 天；账单到期日：{_safe(due_date_text)}；账单金额：{_money(payment_amount)} 元。</p>
    <p>乙方在平台消费时可以根据自身需求提交账期支付申请，甲方有权根据乙方信用状况动态调整账期额度及期限。</p>
  </section>
  <section>
    <h2>四、账期支付约定</h2>
    <p>乙方应按本协议约定按时支付每期应付款。乙方可主动登录平台相关页面进行支付；在系统功能可实现的情况下，平台可在到期付款日发起自动扣款。扣款失败不构成甲方履约瑕疵，乙方应及时主动支付，避免逾期。</p>
  </section>
  <section>
    <h2>五、退换货及违约</h2>
    <p>因商品质量问题或商品与描述不符导致乙方需退换商品或取消订单的，应在签收后 7 日内按平台要求提出。甲方核验后按平台规则处理。定制商品因属个性化产品，除商品存在质量问题或不符定制标准外，不适用七日无理由退货。</p>
    <p>乙方若未能按合同约定按期如数全额支付款项，应承担按违约之日起以未付货款为基数，按照未付货款额每日千分之三计算的违约金；甲方有权要求乙方一次性支付全部款项或收回商品并要求支付占有使用费及折旧损失。</p>
  </section>
  <section>
    <h2>六、信息查询和披露</h2>
    <p>乙方购买商品并申请先发货后支付或账期支付，即视为乙方授权甲方因业务开展需要获取、使用、存储、处理、传输及披露乙方个人信息。为降低甲方风险，乙方需提交身份证正反面照片和个人自拍照供甲方核对真实性。</p>
  </section>
  <section>
    <h2>七、争议处置和送达</h2>
    <p>本合同受中华人民共和国法律管辖与解释。本合同项下争议首先由各方协商解决；协商不成的，由甲方或乙方所在地人民法院管辖。乙方确认姓名、手机号码、身份证地址等联系方式为有效送达地址。</p>
    <p>姓名：{_safe(user.name)}；手机号码：{_safe(user.phone)}；邮寄地址：{_safe(address)}。</p>
  </section>
  <section>
    <h2>八、电子合同的签署与生效</h2>
    <p>乙方授权并同意本协议以电子签名或点击、勾选等方式确认签署。乙方确认本人已仔细阅读并理解本协议全部条款，签署本合同及履行合同义务是独立真实意思表示。</p>
  </section>
  <section class="contract-sign-area">
    <p>甲方（平台）：{_safe(PARTY_A_NAME)}</p>
    <p>法人：{_safe(PARTY_A_LEGAL_PERSON)}</p>
    <p>签订日期：{now.strftime('%Y年%m月%d日')}</p>
    <p>乙方（用户）：{_safe(user.name)}</p>
    <p>身份证：{_safe(user.id_card_num)}</p>
    <p>联系电话：{_safe(user.phone)}</p>
    <p>身份证地址：{_safe(address)}</p>
    <p>签订日期：{now.strftime('%Y年%m月%d日')}</p>
  </section>
</article>
""".strip()
    text_content = "\n".join([f"{label}：{value}" for label, value in rows])
    return {
        "contract_content": html_content,
        "contract_text": text_content,
        "party_b_address": address,
        "product_name": product_name,
        "ecard_face_value": ecard_face_value,
        "rights_price": effective_rights_price,
        "discount_amount": discount_amount,
        "payment_amount": payment_amount,
        "term_days": term_days,
        "due_date_text": due_date_text,
    }


def serialize_purchase_contract(signature: PurchaseContractSignature) -> dict:
    return {
        "id": signature.id,
        "signature_no": signature.signature_no,
        "order_no": signature.order_no,
        "user_id": signature.user_id,
        "loan_id": signature.loan_id,
        "product_id": signature.product_id,
        "contract_title": signature.contract_title,
        "contract_content": signature.contract_content,
        "party_a_name": signature.party_a_name,
        "party_a_legal_person": signature.party_a_legal_person,
        "party_b_name": signature.party_b_name,
        "party_b_id_card": signature.party_b_id_card,
        "party_b_phone": signature.party_b_phone,
        "product_name": signature.product_name,
        "ecard_face_value": signature.ecard_face_value,
        "rights_price": signature.rights_price,
        "discount_amount": signature.discount_amount,
        "payment_amount": signature.payment_amount,
        "term_days": signature.term_days,
        "due_date_text": signature.due_date_text,
        "signed_at": signature.signed_at,
        "ip": signature.ip,
    }
