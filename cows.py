from flask import render_template, Blueprint, request, redirect
from flask_simplelogin import login_required

from models import Cow, Event, Transaction, get_cow_from_tag, db
from setup_utils import get_usernames

cows = Blueprint('cows', __name__, template_folder='templates')

@cows.route("/")
@login_required
def list_cows():
    cow_list = Cow.query.all()
    usernames = get_usernames()
    return render_template("cows.html", cows=cow_list, usernames=usernames)


@cows.route("/cow/<tag_number>")
@login_required
def show_cow(tag_number):
    cow = Cow.query.filter_by(tag_number=tag_number).first()
    if not cow:
        return redirect(request.referrer)
    events = Event.query.all()

    transaction_total = 0
    for event in events:
        for transaction in event.transactions:
            transaction_total += transaction.price

    return render_template("cow.html", cow=cow, cows=Cow.query.all(), events=events, transaction_total=transaction_total)

@cows.route("/new", methods=["POST"])
@login_required
def new_cow():
    date = request.form.get('date')
    born_event_enabled = request.form.get('born_event')
    calved_event_enabled = request.form.get('calved_event')
    dam_tag = request.form.get('dam')
    sire_tag = request.form.get('sire')
    tag_number = request.form.get('tag_number')
    owner = request.form.get('owner')
    sex = request.form.get('sex')

    new_cow_object = Cow(
        dam_id=get_cow_from_tag(dam_tag).cow_id if dam_tag else "",
        sire_id=get_cow_from_tag(sire_tag).cow_id if sire_tag else "",
        owner=owner,
        sex=sex,
        tag_number=tag_number
    )

    if born_event_enabled == 'on':
        born_event = Event(
            date=date, name="Born", description=f"{dam_tag} gave birth to {tag_number}", cows=[new_cow_object])
        db.session.add(born_event)

    if calved_event_enabled == 'on':
        calved_event = Event(date=date, name="Calved", description=f"{dam_tag} gave birth to {tag_number}", cows=[
                             get_cow_from_tag(dam_tag)])
        db.session.add(calved_event)

    db.session.add(new_cow_object)
    db.session.commit()
    return redirect(request.referrer)


@cows.route("/exists/<tag_number>")
@login_required
def cow_exists(tag_number):
    cow = Cow.query.filter_by(tag_number=tag_number).first()

    return "True" if cow else "False"


@cows.route("/change_tag_number", methods=["POST"])
@login_required
def change_tag_number():
    old_tag_number = request.form.get("old_tag_number")
    new_tag_number = request.form.get("new_tag_number")

    cow = get_cow_from_tag(old_tag_number)
    cow.tag_number = new_tag_number
    db.session.commit()
    return redirect("/cows/cow/"+new_tag_number)


@cows.route("/change_sex", methods=["POST"])
@login_required
def change_sex():
    tag_number = request.form.get("tag_number")
    sex = request.form.get("sex")

    cow = get_cow_from_tag(tag_number)
    cow.sex = sex
    db.session.commit()
    return redirect("/cows/cow/"+tag_number)


@cows.route("/delete", methods=["POST"])
@login_required
def delete_cow():
    tag_number = request.form.get("tag_number")
    cow = Cow.query.filter_by(tag_number=tag_number).first()
    db.session.delete(cow)
    db.session.commit()
    return redirect('/cows')


@cows.route("/transfer_ownership", methods=["POST"])
@login_required
def transferOwnership():
    tag_number = request.form.get("tag_number")
    new_owner = request.form.get("newOwner")
    date = request.form.get("date")
    price = request.form.get("price")
    description = request.form.get("description")

    cow = Cow.query.filter_by(tag_number=tag_number).first()
    sale_transaction = Transaction(
        name="Sold", description=f"{cow.owner} sold {tag_number}: {description}", price=price, tofrom=new_owner)
    sale_event = Event(date=date, name="Transfer",
                       description=f"Transfer {cow.tag_number} from {cow.owner} to {new_owner}:\n{description}", cows=[cow], transactions=[sale_transaction])

    cow.owner = new_owner

    db.session.add(sale_event)
    db.session.commit()
    return redirect(request.referrer)


@cows.route("/add_parent", methods=["POST"])
@login_required
def cow_add_parent():
    tag_number = request.form.get("tag_number")
    parent_type = request.form.get("parent_type")
    parent_tag = request.form.get("parent_tag")

    cow = get_cow_from_tag(tag_number)

    if parent_type == "Dam":
        cow.dam_id = get_cow_from_tag(parent_tag).cow_id
    else:
        cow.sire_id = get_cow_from_tag(parent_tag).cow_id
    db.session.commit()
    return redirect(request.referrer)
