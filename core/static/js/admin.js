(function ($) {
    $(document).ready(function () {
        $(".carousel-images").each(function () {
            const carousel = $(this).find(".carousel");
            const nextBtn = $(this).find(".carousel-btn.next-btn");
            const prevBtn = $(this).find(".carousel-btn.prev-btn");

            carousel.carousel();

            nextBtn.on("click", function () {
                carousel.carousel("next");
            });

            prevBtn.on("click", function () {
                carousel.carousel("prev");
            });
        });
    });
})(django.jQuery);



// (function ($) {
//     $(document).ready(function () {
//         $(".carousel-images").each(function () {
//             const images = $(this).find(".carousel-image");
//             let currentIndex = 0;

//             function showImage(index) {
//                 images.hide();
//                 images.eq(index).show();
//             }

//             function nextImage() {
//                 currentIndex = (currentIndex + 1) % images.length;
//                 showImage(currentIndex);
//             }

//             function prevImage() {
//                 currentIndex = (currentIndex - 1 + images.length) % images.length;
//                 showImage(currentIndex);
//             }

//             showImage(currentIndex);

//             $(this).find(".next-btn").on("click", function () {
//                 nextImage();
//             });

//             $(this).find(".prev-btn").on("click", function () {
//                 prevImage();
//             });
//         });
//     });
// })(django.jQuery);