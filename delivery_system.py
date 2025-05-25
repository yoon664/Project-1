# 음식 배달 시스템 샘플 코드
from datetime import datetime
from typing import List, Dict
from enum import Enum

class OrderStatus(Enum):
    PENDING = "주문대기"
    CONFIRMED = "주문확인"
    PREPARING = "조리중"
    READY = "조리완료"
    DELIVERING = "배달중"
    DELIVERED = "배달완료"

class PaymentStatus(Enum):
    PENDING = "결제대기"
    COMPLETED = "결제완료"
    FAILED = "결제실패"

# 사용자 클래스
class User:
    def __init__(self, user_id: str, name: str, phone: str, address: str):
        self.user_id = user_id
        self.name = name
        self.phone = phone
        self.address = address
    
    def login(self, app):
        print(f"[사용자] {self.name}님이 로그인했습니다.")
        return app.show_main_screen()
    
    def select_restaurant(self, app, restaurant_id: str):
        print(f"[사용자] 음식점 선택: {restaurant_id}")
        return app.get_menu(restaurant_id)
    
    def add_to_cart(self, app, menu_item: Dict, quantity: int):
        print(f"[사용자] 장바구니 추가: {menu_item['name']} x {quantity}")
        return app.add_to_cart(menu_item, quantity)
    
    def place_order(self, app):
        print(f"[사용자] 주문 요청")
        return app.process_order(self)
    
    def confirm_delivery(self, order_id: str):
        print(f"[사용자] 배달 완료 확인: {order_id}")
        return True
    
    def write_review(self, order_id: str, rating: int, comment: str):
        print(f"[사용자] 리뷰 작성: {rating}점 - {comment}")
        return {"order_id": order_id, "rating": rating, "comment": comment}

# 배달앱 클래스
class DeliveryApp:
    def __init__(self):
        self.cart = []
        self.restaurants = {}
        self.orders = {}
        self.payment_system = PaymentSystem()
        self.delivery_system = DeliverySystem()
    
    def show_main_screen(self):
        print("[배달앱] 메인 화면을 표시합니다.")
        return "메인 화면 로드 완료"
    
    def register_restaurant(self, restaurant):
        self.restaurants[restaurant.restaurant_id] = restaurant
        print(f"[배달앱] 음식점 등록: {restaurant.name}")
    
    def get_menu(self, restaurant_id: str):
        if restaurant_id in self.restaurants:
            restaurant = self.restaurants[restaurant_id]
            menu = restaurant.get_menu()
            print(f"[배달앱] 메뉴 정보 수신: {len(menu)}개 메뉴")
            return menu
        return []
    
    def add_to_cart(self, menu_item: Dict, quantity: int):
        cart_item = {
            "menu_item": menu_item,
            "quantity": quantity,
            "subtotal": menu_item["price"] * quantity
        }
        self.cart.append(cart_item)
        print(f"[배달앱] 장바구니 업데이트 완료")
        return self.cart
    
    def process_order(self, user: User):
        if not self.cart:
            print("[배달앱] 장바구니가 비어있습니다.")
            return None
        
        # 결제 처리
        total_amount = sum(item["subtotal"] for item in self.cart)
        payment_result = self.payment_system.process_payment(user.user_id, total_amount)
        
        if payment_result["status"] == PaymentStatus.COMPLETED:
            # 주문 생성
            order_id = f"ORDER_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            order = Order(order_id, user, self.cart.copy(), total_amount)
            self.orders[order_id] = order
            
            # 음식점에 주문 전달
            restaurant_id = self.cart[0]["menu_item"]["restaurant_id"]
            restaurant = self.restaurants[restaurant_id]
            restaurant.receive_order(order)
            
            # 장바구니 초기화
            self.cart.clear()
            
            print(f"[배달앱] 주문 완료: {order_id}")
            return order
        else:
            print("[배달앱] 결제 실패")
            return None
    
    def update_order_status(self, order_id: str, status: OrderStatus):
        if order_id in self.orders:
            self.orders[order_id].status = status
            print(f"[배달앱] 주문 상태 업데이트: {order_id} -> {status.value}")
            
            # 배달 시작 시 배달 시스템에 요청
            if status == OrderStatus.READY:
                order = self.orders[order_id]
                self.delivery_system.start_delivery(order)

# 음식점 클래스
class Restaurant:
    def __init__(self, restaurant_id: str, name: str, address: str):
        self.restaurant_id = restaurant_id
        self.name = name
        self.address = address
        self.menu = []
        self.current_orders = {}
    
    def add_menu_item(self, name: str, price: int, description: str = ""):
        menu_item = {
            "name": name,
            "price": price,
            "description": description,
            "restaurant_id": self.restaurant_id
        }
        self.menu.append(menu_item)
    
    def get_menu(self):
        print(f"[음식점] {self.name} 메뉴 정보 제공")
        return self.menu
    
    def receive_order(self, order):
        print(f"[음식점] 주문 접수: {order.order_id}")
        self.current_orders[order.order_id] = order
        order.status = OrderStatus.CONFIRMED
        
        # 조리 시작
        self.start_cooking(order.order_id)
    
    def start_cooking(self, order_id: str):
        print(f"[음식점] 조리 시작: {order_id}")
        if order_id in self.current_orders:
            self.current_orders[order_id].status = OrderStatus.PREPARING
    
    def finish_cooking(self, order_id: str, app: DeliveryApp):
        print(f"[음식점] 조리 완료: {order_id}")
        if order_id in self.current_orders:
            app.update_order_status(order_id, OrderStatus.READY)
    
    def hand_over_food(self, order_id: str):
        print(f"[음식점] 음식 전달: {order_id}")
        return self.current_orders.get(order_id)

# 결제 시스템 클래스
class PaymentSystem:
    def __init__(self):
        self.transactions = {}
    
    def process_payment(self, user_id: str, amount: int):
        transaction_id = f"PAY_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"[결제시스템] 결제 처리 시작: {amount}원")
        
        # 실제로는 외부 결제 게이트웨이와 통신
        # 여기서는 단순히 성공으로 처리
        transaction = {
            "transaction_id": transaction_id,
            "user_id": user_id,
            "amount": amount,
            "status": PaymentStatus.COMPLETED,
            "timestamp": datetime.now()
        }
        
        self.transactions[transaction_id] = transaction
        print(f"[결제시스템] 결제 완료: {transaction_id}")
        
        return transaction

# 배달 시스템 클래스
class DeliverySystem:
    def __init__(self):
        self.active_deliveries = {}
        self.delivery_drivers = ["기사1", "기사2", "기사3"]
    
    def start_delivery(self, order):
        print(f"[배달시스템] 배달 시작: {order.order_id}")
        
        # 배달기사 배정 (단순화)
        driver = self.delivery_drivers[0] if self.delivery_drivers else "배달기사"
        
        delivery_info = {
            "order_id": order.order_id,
            "driver": driver,
            "pickup_address": "음식점 주소",
            "delivery_address": order.user.address,
            "status": "픽업완료"
        }
        
        self.active_deliveries[order.order_id] = delivery_info
        order.status = OrderStatus.DELIVERING
        
        print(f"[배달시스템] {driver}이(가) 배달을 시작합니다.")
        
        # 배달 완료 시뮬레이션
        self.complete_delivery(order.order_id)
    
    def complete_delivery(self, order_id: str):
        print(f"[배달시스템] 배달 완료: {order_id}")
        if order_id in self.active_deliveries:
            self.active_deliveries[order_id]["status"] = "배달완료"

# 주문 클래스
class Order:
    def __init__(self, order_id: str, user: User, cart_items: List, total_amount: int):
        self.order_id = order_id
        self.user = user
        self.cart_items = cart_items
        self.total_amount = total_amount
        self.status = OrderStatus.PENDING
        self.created_at = datetime.now()

# 시스템 사용 예제
def main():
    print("=== 음식 배달 시스템 시뮬레이션 ===\n")
    
    # 시스템 초기화
    app = DeliveryApp()
    
    # 음식점 등록
    restaurant = Restaurant("REST001", "맛있는 치킨집", "서울시 강남구")
    restaurant.add_menu_item("후라이드 치킨", 18000, "바삭한 후라이드 치킨")
    restaurant.add_menu_item("양념치킨", 19000, "달콤한 양념 치킨")
    app.register_restaurant(restaurant)
    
    # 사용자 생성
    user = User("USER001", "김철수", "010-1234-5678", "서울시 서초구")
    
    # 시퀀스 다이어그램 기반 실행 흐름
    print("\n1. 사용자 로그인")
    user.login(app)
    
    print("\n2. 음식점 선택 및 메뉴 조회")
    menu = user.select_restaurant(app, "REST001")
    
    print("\n3. 음식 선택 및 장바구니 담기")
    user.add_to_cart(app, menu[0], 1)  # 후라이드 치킨 1개
    user.add_to_cart(app, menu[1], 1)  # 양념치킨 1개
    
    print("\n4. 주문 및 결제")
    order = user.place_order(app)
    
    if order:
        print(f"\n5. 조리 과정")
        restaurant.finish_cooking(order.order_id, app)
        
        print(f"\n6. 배달 완료 확인")
        user.confirm_delivery(order.order_id)
        
        print(f"\n7. 리뷰 작성")
        user.write_review(order.order_id, 5, "맛있게 잘 먹었습니다!")
    
    print("\n=== 시뮬레이션 완료 ===")

if __name__ == "__main__":
    main()